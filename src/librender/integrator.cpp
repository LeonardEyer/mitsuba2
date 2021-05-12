#include <thread>
#include <mutex>

#include <enoki/morton.h>
#include <mitsuba/core/profiler.h>
#include <mitsuba/core/progress.h>
#include <mitsuba/core/spectrum.h>
#include <mitsuba/core/timer.h>
#include <mitsuba/core/util.h>
#include <mitsuba/core/warp.h>
#include <mitsuba/render/film.h>
#include <mitsuba/render/integrator.h>
#include <mitsuba/render/sampler.h>
#include <mitsuba/render/sensor.h>
#include <mitsuba/render/spiral.h>
#include <tbb/blocked_range.h>
#include <tbb/parallel_for.h>
#include <mutex>

NAMESPACE_BEGIN(mitsuba)

// -----------------------------------------------------------------------------

MTS_VARIANT Integrator<Float, Spectrum>::Integrator(const Properties & props)
    : m_stop(false) {
    m_timeout = props.float_("timeout", -1.f);
}

MTS_VARIANT std::vector<std::string> Integrator<Float, Spectrum>::aov_names() const {
    return { };
}

// -----------------------------------------------------------------------------

MTS_VARIANT SamplingIntegrator<Float, Spectrum>::SamplingIntegrator(const Properties &props)
    : Base(props) {

    m_block_size = (uint32_t) props.size_("block_size", 0);
    uint32_t block_size = math::round_to_power_of_two(m_block_size);
    if (m_block_size > 0 && block_size != m_block_size) {
        Log(Warn, "Setting block size from %i to next higher power of two: %i", m_block_size,
            block_size);
        m_block_size = block_size;
    }

    m_samples_per_pass = (uint32_t) props.size_("samples_per_pass", (size_t) -1);

    /// Disable direct visibility of emitters if needed
    m_hide_emitters = props.bool_("hide_emitters", false);
}

MTS_VARIANT SamplingIntegrator<Float, Spectrum>::~SamplingIntegrator() { }

MTS_VARIANT void SamplingIntegrator<Float, Spectrum>::cancel() {
    m_stop = true;
}

MTS_VARIANT bool SamplingIntegrator<Float, Spectrum>::render(Scene *scene, Sensor *sensor) {
    ScopedPhase sp(ProfilerPhase::Render);
    m_stop = false;

    ref<Film> film = sensor->film();
    ScalarVector2i film_size = film->crop_size();

    size_t total_spp        = sensor->sampler()->sample_count();
    size_t samples_per_pass = (m_samples_per_pass == (size_t) -1)
                               ? total_spp : std::min((size_t) m_samples_per_pass, total_spp);
    if ((total_spp % samples_per_pass) != 0)
        Throw("sample_count (%d) must be a multiple of samples_per_pass (%d).",
              total_spp, samples_per_pass);

    size_t n_passes = (total_spp + samples_per_pass - 1) / samples_per_pass;

    std::vector<std::string> channels = aov_names();
    bool has_aovs = !channels.empty();

    // Insert default channels and set up the film
    for (size_t i = 0; i < 5; ++i)
        channels.insert(channels.begin() + i, std::string(1, "XYZAW"[i]));
    film->prepare(channels);

    if constexpr (!is_cuda_array_v<Float>) {
        /// Render on the CPU using a spiral pattern
        size_t n_threads = __global_thread_count;
        Log(Info, "Starting render job (%ix%i, %i sample%s,%s %i thread%s)",
            film_size.x(), film_size.y(),
            total_spp, total_spp == 1 ? "" : "s",
            n_passes > 1 ? tfm::format(" %d passes,", n_passes) : "",
            n_threads, n_threads == 1 ? "" : "s");

        if (m_timeout > 0.f)
            Log(Info, "Timeout specified: %.2f seconds.", m_timeout);

        // Find a good block size to use for splitting up the total workload.
        if (m_block_size == 0) {
            uint32_t block_size = MTS_BLOCK_SIZE;
            while (true) {
                if (block_size == 1 || hprod((film_size + block_size - 1) / block_size) >= n_threads)
                    break;
                block_size /= 2;
            }
            m_block_size = block_size;
        }

        Spiral spiral(film, m_block_size, n_passes);

        ThreadEnvironment env;
        ref<ProgressReporter> progress = new ProgressReporter("Rendering");
        std::mutex mutex;

        // Total number of blocks to be handled, including multiple passes.
        size_t total_blocks = spiral.block_count() * n_passes,
               blocks_done = 0;

        m_render_timer.reset();
        tbb::parallel_for(
            tbb::blocked_range<size_t>(0, total_blocks, 1),
            [&](const tbb::blocked_range<size_t> &range) {
                ScopedSetThreadEnvironment set_env(env);
                ref<Sampler> sampler = sensor->sampler()->clone();
                ref<ImageBlock> block = new ImageBlock(m_block_size, channels.size(),
                                                       film->reconstruction_filter(),
                                                       !has_aovs);
                scoped_flush_denormals flush_denormals(true);
                std::unique_ptr<Float[]> aovs(new Float[channels.size()]);

                // For each block
                for (auto i = range.begin(); i != range.end() && !should_stop(); ++i) {
                    auto [offset, size, block_id] = spiral.next_block();
                    Assert(hprod(size) != 0);
                    block->set_size(size);
                    block->set_offset(offset);

                    // Ensure that the sample generation is fully deterministic
                    sampler->seed(block_id);

                    render_block(scene, sensor, sampler, block,
                                 aovs.get(), samples_per_pass);

                    film->put(block);

                    /* Critical section: update progress bar */ {
                        std::lock_guard<std::mutex> lock(mutex);
                        blocks_done++;
                        progress->update(blocks_done / (ScalarFloat) total_blocks);
                    }
                }
            }
        );
    } else {
        ref<Sampler> sampler = sensor->sampler();

        ScalarFloat diff_scale_factor = rsqrt((ScalarFloat) sampler->sample_count());
        ScalarUInt32 total_sample_count = hprod(film_size) * (uint32_t) samples_per_pass;
        if (sampler->wavefront_size() != total_sample_count)
            sampler->seed(arange<UInt64>(total_sample_count));

        UInt32 idx = arange<UInt32>(total_sample_count);
        if (samples_per_pass != 1)
            idx /= (uint32_t) samples_per_pass;

        ref<ImageBlock> block = new ImageBlock(film_size, channels.size(),
                                               film->reconstruction_filter(),
                                               !has_aovs);
        block->clear();
        Vector2f pos = Vector2f(Float(idx % uint32_t(film_size[0])),
                                Float(idx / uint32_t(film_size[0])));
        std::vector<Float> aovs(channels.size());

        for (size_t i = 0; i < n_passes; i++)
            render_sample(scene, sensor, sampler, block, aovs.data(),
                          pos, diff_scale_factor);

        film->put(block);
    }

    if (!m_stop)
        Log(Info, "Rendering finished. (took %s)",
            util::time_string(m_render_timer.value(), true));

    return !m_stop;
}

MTS_VARIANT void SamplingIntegrator<Float, Spectrum>::render_block(const Scene *scene,
                                                                   const Sensor *sensor,
                                                                   Sampler *sampler,
                                                                   ImageBlock *block,
                                                                   Float *aovs,
                                                                   size_t sample_count_) const {
    block->clear();
    uint32_t pixel_count  = (uint32_t)(m_block_size * m_block_size),
             sample_count = (uint32_t)(sample_count_ == (size_t) -1
                                           ? sampler->sample_count()
                                           : sample_count_);

    ScalarFloat diff_scale_factor = rsqrt((ScalarFloat) sampler->sample_count());

    if constexpr (!is_array_v<Float>) {
        for (uint32_t i = 0; i < pixel_count && !should_stop(); ++i) {
            ScalarPoint2u pos = enoki::morton_decode<ScalarPoint2u>(i);
            if (any(pos >= block->size()))
                continue;

            pos += block->offset();
            for (uint32_t j = 0; j < sample_count && !should_stop(); ++j) {
                render_sample(scene, sensor, sampler, block, aovs,
                              pos, diff_scale_factor);
            }
        }
    } else if constexpr (is_array_v<Float> && !is_cuda_array_v<Float>) {
        for (auto [index, active] : range<UInt32>(pixel_count * sample_count)) {
            if (should_stop())
                break;
            Point2u pos = enoki::morton_decode<Point2u>(index / UInt32(sample_count));
            active &= !any(pos >= block->size());
            pos += block->offset();
            render_sample(scene, sensor, sampler, block, aovs, pos, diff_scale_factor, active);
        }
    } else {
        ENOKI_MARK_USED(scene);
        ENOKI_MARK_USED(sensor);
        ENOKI_MARK_USED(aovs);
        ENOKI_MARK_USED(diff_scale_factor);
        ENOKI_MARK_USED(pixel_count);
        ENOKI_MARK_USED(sample_count);
        Throw("Not implemented for CUDA arrays.");
    }
}

MTS_VARIANT void SamplingIntegrator<Float, Spectrum>::render_sample(
    const Scene *scene, const Sensor *sensor, Sampler *sampler, ImageBlock *block,
    Float *aovs, const Vector2f &pos, ScalarFloat diff_scale_factor, Mask active) const {
    Vector2f position_sample = pos + sampler->next_2d(active);

    Point2f aperture_sample(.5f);
    if (sensor->needs_aperture_sample())
        aperture_sample = sampler->next_2d(active);

    Float time = sensor->shutter_open();
    if (sensor->shutter_open_time() > 0.f)
        time += sampler->next_1d(active) * sensor->shutter_open_time();

    Float wavelength_sample = sampler->next_1d(active);

    Vector2f adjusted_position =
        (position_sample - sensor->film()->crop_offset()) /
        sensor->film()->crop_size();

    auto [ray, ray_weight] = sensor->sample_ray_differential(
        time, wavelength_sample, adjusted_position, aperture_sample);

    ray.scale_differential(diff_scale_factor);

    const Medium *medium = sensor->medium();
    std::pair<Spectrum, Mask> result = sample(scene, sampler, ray, medium, aovs + 5, active);
    result.first = ray_weight * result.first;

    UnpolarizedSpectrum spec_u = depolarize(result.first);

    Color3f xyz;
    if constexpr (is_monochromatic_v<Spectrum>) {
        xyz = spec_u.x();
    } else if constexpr (is_rgb_v<Spectrum>) {
        xyz = srgb_to_xyz(spec_u, active);
    } else {
        static_assert(is_spectral_v<Spectrum>);
        xyz = spectrum_to_xyz(spec_u, ray.wavelengths, active);
    }

    aovs[0] = xyz.x();
    aovs[1] = xyz.y();
    aovs[2] = xyz.z();
    aovs[3] = select(result.second, Float(1.f), Float(0.f));
    aovs[4] = 1.f;

    block->put(position_sample, aovs, active);
}

MTS_VARIANT std::pair<Spectrum, typename SamplingIntegrator<Float, Spectrum>::Mask>
SamplingIntegrator<Float, Spectrum>::sample(const Scene * /* scene */,
                                            Sampler * /* sampler */,
                                            const RayDifferential3f & /* ray */,
                                            const Medium * /* medium */,
                                            Float * /* aovs */,
                                            Mask /* active */) const {
    NotImplementedError("sample");
}

// -----------------------------------------------------------------------------

MTS_VARIANT MonteCarloIntegrator<Float, Spectrum>::MonteCarloIntegrator(const Properties &props)
    : Base(props) {
    /// Depth to begin using russian roulette
    m_rr_depth = props.int_("rr_depth", 5);
    if (m_rr_depth <= 0)
        Throw("\"rr_depth\" must be set to a value greater than zero!");

    /*  Longest visualized path depth (``-1 = infinite``). A value of \c 1 will
        visualize only directly visible light sources. \c 2 will lead to
        single-bounce (direct-only) illumination, and so on. */
    m_max_depth = props.int_("max_depth", -1);
    if (m_max_depth < 0 && m_max_depth != -1)
        Throw("\"max_depth\" must be set to -1 (infinite) or a value >= 0");
}

MTS_VARIANT MonteCarloIntegrator<Float, Spectrum>::~MonteCarloIntegrator() { }

// -----------------------------------------------------------------------------

MTS_VARIANT TimeDependentIntegrator<Float, Spectrum>::TimeDependentIntegrator(const Properties &props)
    : Base(props) {

    m_time_step_count = 0;

    // TODO: consider moving those parameters to the base class.
    m_samples_per_pass = (uint32_t) props.size_("samples_per_pass", (size_t) -1);
    m_hide_emitters = props.bool_("hide_emitters", false);

    m_rr_depth = props.int_("rr_depth", 5);
    if (m_rr_depth <= 0)
        Throw("\"rr_depth\" must be set to a value greater than zero!");

    m_max_depth = props.int_("max_depth", -1);
    if (m_max_depth < 0 && m_max_depth != -1)
        Throw("\"max_depth\" must be set to -1 (infinite) or a value >= 0");

    m_max_time = props.float_("max_time", 1.0f);

    if (m_max_time <= 0)
        Throw("\"max_time\" must be set to a value greater than zero!");


    std::vector<std::string> wavelengths_str =
        string::tokenize(props.string("wavelength_bins"), " ,");

    m_wav_bin_count = wavelengths_str.size();

    // Allocate space
    m_wavelength_bins = zero<DynamicBuffer<Float>>(wavelengths_str.size());

    // Copy and convert to wavelengths
    for (size_t i = 0; i < wavelengths_str.size(); ++i) {
        try {
            Float wav = std::stod(wavelengths_str[i]);
            scatter(m_wavelength_bins, wav, UInt32(i));
        } catch (...) {
            Throw("Could not parse floating point value '%s'",
                  wavelengths_str[i]);
        }
    }

}

MTS_VARIANT TimeDependentIntegrator<Float, Spectrum>::~TimeDependentIntegrator() { }

MTS_VARIANT
std::pair<Spectrum, typename TimeDependentIntegrator<Float, Spectrum>::Mask>
    TimeDependentIntegrator<Float, Spectrum>::trace_acoustic_ray(const Scene *scene,
                                                             Sampler *sampler,
                                                             const Ray3f &ray,
                                                             Histogram *hist,
                                                             const UInt32 band_id,
                                                             Mask active) const {
    NotImplementedError("trace_acoustic_ray");
}

MTS_VARIANT bool
TimeDependentIntegrator<Float, Spectrum>::render(Scene *scene, Sensor *sensor) {
    ScopedPhase sp(ProfilerPhase::Render);
    m_stop = false;

    ref<Film> film          = sensor->film();

    auto film_size          = film->size();
    m_time_step_count       = film_size.x();

    size_t total_spp        = sensor->sampler()->sample_count();
    size_t samples_per_pass = (m_samples_per_pass == (size_t) -1)
                              ? total_spp : std::min((size_t) m_samples_per_pass, total_spp);

    if ((total_spp % samples_per_pass) != 0)
        Throw("sample_count (%d) must be a multiple of samples_per_pass (%d).",
              total_spp, samples_per_pass);

    size_t n_passes = (total_spp + samples_per_pass - 1) / samples_per_pass;

    m_render_timer.reset();
    if constexpr (!is_cuda_array_v<Float>) {

        /// Render on the CPU using a spiral pattern
        size_t n_threads = __global_thread_count;
        Log(Info, "Starting render job (%ix%i, %i sample%s,%s %i thread%s)",
            film_size.x(), film_size.y(), total_spp, total_spp == 1 ? "" : "s",
            n_passes > 1 ? tfm::format(" %d passes,", n_passes) : "",
            n_threads, n_threads == 1 ? "" : "s");

        ThreadEnvironment env;
        ref<ProgressReporter> progress = new ProgressReporter("Rendering");
        std::mutex mutex;

        size_t total_bands = film_size.y() * n_passes, bands_done = 0;

        // Simulate each frequency band and time step times spp
        tbb::parallel_for(size_t(0), total_bands, [&](size_t i) {
            ScopedSetThreadEnvironment set_env(env);

            ref<Sampler> sampler = sensor->sampler()->clone();

            size_t band_id = i / n_passes;

            ref<Histogram> hist = new Histogram(film_size, 1);

            scoped_flush_denormals flush_denormals(true);

            hist->set_offset({ 0, band_id });
            hist->clear();

            render_band(scene, sensor, sampler, hist, samples_per_pass, band_id);

            film->put(hist);

            /* Critical section: update progress bar */ {
                std::lock_guard<std::mutex> lock(mutex);
                bands_done++;
                progress->update(bands_done / (ScalarFloat) total_bands);
            }
        });
    } else {
        ref<ProgressReporter> progress = new ProgressReporter("Rendering");

        ref<Sampler> sampler = sensor->sampler();

        ScalarUInt32 total_sample_count = hprod(film_size) * (uint32_t) samples_per_pass;
        if (sampler->wavefront_size() != total_sample_count)
            sampler->seed(arange<UInt64>(total_sample_count));

        UInt32 idx = arange<UInt32>(total_sample_count);
        if (samples_per_pass != 1)
            idx /= (uint32_t) samples_per_pass;

        UInt32 band_id = 0;
        if (film_size.x() != 1)
            band_id = idx % film_size.x();

        ref<Histogram> hist = new Histogram(film_size, 1);
        hist->clear();

        for (size_t i = 0; i < n_passes; i++) {
            render_sample(scene, sensor, sampler, hist, band_id);
            progress->update( (i + 1) / (ScalarFloat) n_passes);
        }

        film->put(hist);
    }

    if (!m_stop)
        Log(Info, "Rendering finished. (took %s)",
            util::time_string(m_render_timer.value(), true));

    return !m_stop;
}

MTS_VARIANT void TimeDependentIntegrator<Float, Spectrum>::render_band(const Scene *scene,
                                                                   const Sensor *sensor,
                                                                   Sampler *sampler,
                                                                   Histogram *hist,
                                                                   size_t sample_count_,
                                                                   const size_t band_id) const {
    auto sample_count = (uint32_t)(sample_count_ == (size_t) -1
                                       ? sampler->sample_count()
                                       : sample_count_);

    hist->clear();

    if constexpr (!is_array_v<Float>) {
        for (uint32_t i = 0; i < m_time_step_count; ++i) {
            sampler->seed(band_id * m_time_step_count + i);
            for (uint32_t j = 0; j < sample_count; ++j) {
                render_sample(scene, sensor, sampler, hist, band_id);
            }
        }
    } else if constexpr (is_array_v<Float> && !is_cuda_array_v<Float>) {
        // Ensure that the sample generation is fully deterministic
        sampler->seed(band_id);

        for (auto [index, active] : range<UInt32>(m_time_step_count * sample_count)) {
            render_sample(scene, sensor, sampler, hist, band_id);
        }
    } else {
        ENOKI_MARK_USED(scene);
        ENOKI_MARK_USED(sensor);
        ENOKI_MARK_USED(band_id);
        ENOKI_MARK_USED(sample_count);
        Throw("Not implemented for CUDA arrays.");
    }
}


MTS_VARIANT void
TimeDependentIntegrator<Float, Spectrum>::render_sample(const Scene *scene,
                                                        const Sensor *sensor,
                                                        Sampler *sampler,
                                                        Histogram *hist,
                                                        const UInt32 band_id,
                                                        Mask active) const {

    Point2f direction_sample = sampler->next_2d(active);

    Float wavelength_sample = gather<Float>(m_wavelength_bins, band_id, active);

    auto [ray, ray_weight] = sensor->sample_ray(0, wavelength_sample, { 0, 0 }, direction_sample);

    trace_acoustic_ray(scene, sampler, ray, hist, band_id, active);

}

MTS_VARIANT void TimeDependentIntegrator<Float, Spectrum>::cancel() {
    m_stop = true;
}


MTS_IMPLEMENT_CLASS_VARIANT(Integrator, Object, "integrator")
MTS_IMPLEMENT_CLASS_VARIANT(SamplingIntegrator, Integrator)
MTS_IMPLEMENT_CLASS_VARIANT(MonteCarloIntegrator, SamplingIntegrator)
MTS_IMPLEMENT_CLASS_VARIANT(TimeDependentIntegrator, Integrator)

MTS_INSTANTIATE_CLASS(Integrator)
MTS_INSTANTIATE_CLASS(SamplingIntegrator)
MTS_INSTANTIATE_CLASS(MonteCarloIntegrator)
MTS_INSTANTIATE_CLASS(TimeDependentIntegrator)
NAMESPACE_END(mitsuba)