#include <enoki/stl.h>
#include <mitsuba/core/properties.h>
#include <mitsuba/core/ray.h>
#include <mitsuba/render/bsdf.h>
#include <mitsuba/render/emitter.h>
#include <mitsuba/render/integrator.h>
#include <mitsuba/render/records.h>
#include <random>

NAMESPACE_BEGIN(mitsuba)

template <typename Float, typename Spectrum>
class AcousticPathIntegrator : public TimeDependentIntegrator<Float, Spectrum> {
public:
    MTS_IMPORT_BASE(TimeDependentIntegrator, m_stop,
                    m_max_time, m_wavelength_bins, m_time_step_count)
    MTS_IMPORT_TYPES(Scene, Sensor, Sampler, Medium, Emitter, EmitterPtr, BSDF,
                     BSDFPtr, Histogram)

    AcousticPathIntegrator(const Properties &props) : Base(props) {}

    std::pair<Spectrum, Mask> sample(const Scene *scene, Sampler *sampler,
                                     const RayDifferential3f &ray_,
                                     Histogram * hist,
                                     const Medium * /* medium */,
                                     Float * /* aovs */,
                                     Mask active) const override {
        MTS_MASKED_FUNCTION(ProfilerPhase::SamplingIntegratorSample, active);

        RayDifferential3f ray = ray_;

        Float time = ray.time;

        // Tracks radiance scaling due to index of refraction changes
        Float eta(1.f);

        // MIS weight for intersected emitters (set by prev. iteration)
        Float emission_weight(1.f);

        Spectrum throughput(1.f);//, result(0.f);

        // ---------------------- First intersection ----------------------

        SurfaceInteraction3f si = scene->ray_intersect(ray, active);
        Mask valid_ray          = si.is_valid();
        EmitterPtr emitter      = si.emitter(scene);

        for (int depth = 1;; ++depth) {

           // Update traveled time
           time += select(si.is_valid(), si.t / MTS_SOUND_SPEED, math::Infinity<Float>);

            // medium absorption operator
            //throughput *= enoki::exp( - 0.1151f * alpha * si.t);

            // ---------------- Intersection with sensors ----------------
            if (any_or<true>(neq(emitter, nullptr))) {
                //result[active] += emission_weight * throughput * emitter->eval(si, active);
                throughput[active] *= emission_weight * emitter->eval(si, active);
                // Logging the result
                hist->put(time, ray.wavelengths, throughput, active);

                return { throughput, active };
            }

            active &= si.is_valid();

            // Stop if we've exceeded the number of requested bounces, or
            // if there are no more active lanes. Only do this latter check
            // in GPU mode when the number of requested bounces is infinite
            // since it causes a costly synchronization.
            if (any(time >= (uint32_t) m_max_time) ||
                ((!is_cuda_array_v<Float> || m_max_time < 0) && none(active)))
                break;

            // --------------------- Emitter sampling ---------------------

            BSDFContext ctx;
            BSDFPtr bsdf = si.bsdf(ray);
            Mask active_e = active && has_flag(bsdf->flags(), BSDFFlags::Smooth);

            if (likely(any_or<true>(active_e))) {
                auto [ds, emitter_val] = scene->sample_emitter_direction(
                    si, sampler->next_2d(active_e), true, active_e);
                active_e &= neq(ds.pdf, 0.f);

                // Query the BSDF for that emitter-sampled direction
                Vector3f wo = si.to_local(ds.d);
                Spectrum bsdf_val = bsdf->eval(ctx, si, wo, active_e);
                bsdf_val = si.to_world_mueller(bsdf_val, -wo, si.wi);

                // Determine density of sampling that same direction using BSDF sampling
                Float bsdf_pdf = bsdf->pdf(ctx, si, wo, active_e);

                Float mis = select(ds.delta, 1.f, mis_weight(ds.pdf, bsdf_pdf));

                //result[active_e] += mis * throughput * bsdf_val * emitter_val;
                Spectrum expected_throughput = throughput;
                expected_throughput[active_e] *= mis * bsdf_val * emitter_val;

                // Logging the result
                Float expected_time = (ds.dist / MTS_SOUND_SPEED) + time;
                hist->put(expected_time, ray.wavelengths, expected_throughput, active_e);

            }

            // ----------------------- BSDF sampling ----------------------

            // Sample BSDF * cos(theta)
            auto [bs, bsdf_val] = bsdf->sample(ctx, si, sampler->next_1d(active),
                                               sampler->next_2d(active), active);
            bsdf_val = si.to_world_mueller(bsdf_val, -bs.wo, si.wi);

            throughput = throughput * bsdf_val;
            active &= any(neq(depolarize(throughput), 0.f));
            if (none_or<false>(active))
                break;

            eta *= bs.eta;

            // Intersect the BSDF ray against the scene geometry
            ray = si.spawn_ray(si.to_world(bs.wo));
            SurfaceInteraction3f si_bsdf = scene->ray_intersect(ray, active);

            /* Determine probability of having sampled that same
               direction using emitter sampling. */
            emitter = si_bsdf.emitter(scene, active);
            DirectionSample3f ds(si_bsdf, si);
            ds.object = emitter;

            if (any_or<true>(neq(emitter, nullptr))) {
                Float emitter_pdf =
                    select(neq(emitter, nullptr) && !has_flag(bs.sampled_type, BSDFFlags::Delta),
                           scene->pdf_emitter_direction(si, ds),
                           0.f);

                emission_weight = mis_weight(bs.pdf, emitter_pdf);
            }

            si = std::move(si_bsdf);
        }

        return { throughput, valid_ray };
    }

    //! @}
    // =============================================================

    std::string to_string() const override {
        std::ostringstream oss;
        oss << "AcousticPathIntegrator[" << std::endl
            << "  stop = " << m_stop << "," << std::endl
            << "  max_time = " << m_max_time << "," << std::endl
            << "  wavelength_bins = " << m_wavelength_bins;
        oss << std::endl << "]";
        return oss.str();
    }

    Float mis_weight(Float pdf_a, Float pdf_b) const {
        pdf_a *= pdf_a;
        pdf_b *= pdf_b;
        return select(pdf_a > 0.f, pdf_a / (pdf_a + pdf_b), 0.f);
    }

    MTS_DECLARE_CLASS()
};

MTS_IMPLEMENT_CLASS_VARIANT(AcousticPathIntegrator, TimeDependentIntegrator)
MTS_EXPORT_PLUGIN(AcousticPathIntegrator, "Acoustic Path Tracer integrator");
NAMESPACE_END(mitsuba)
