#include <enoki/stl.h>
#include <iostream>
#include <mitsuba/core/properties.h>
#include <mitsuba/core/ray.h>
#include <mitsuba/render/bsdf.h>
#include <mitsuba/render/emitter.h>
#include <mitsuba/render/integrator.h>
#include <mitsuba/render/records.h>
#include <random>
#include <map>

//define MTS_DEBUG_ACOUSTIC_PATHS "/tmp/ptracer.obj"
#if defined(MTS_DEBUG_ACOUSTIC_PATHS)
#include <fstream>
namespace {
size_t export_counter = 0;
size_t path_counter = 0;
} // namespace
#endif

NAMESPACE_BEGIN(mitsuba)

template <typename Float, typename Spectrum>
class AcousticPathIntegrator : public TimeDependentIntegrator<Float, Spectrum> {
public:
    MTS_IMPORT_BASE(TimeDependentIntegrator, m_stop, m_max_time,
                    m_max_depth, m_wavelength_bins, m_time_step_count)
    MTS_IMPORT_TYPES(Scene, Sensor, Sampler, Medium, Emitter, EmitterPtr, BSDF,
                     BSDFPtr, Histogram)

    AcousticPathIntegrator(const Properties &props) : Base(props) {}

    std::pair<Spectrum, Mask> trace_acoustic_ray(const Scene *scene, Sampler *sampler,
                                     const RayDifferential3f &ray_,
                                     Histogram * hist,
                                     const UInt32 band_id,
                                     Mask active) const override {
        MTS_MASKED_FUNCTION(ProfilerPhase::SamplingIntegratorSample, active);

#if defined(MTS_DEBUG_ACOUSTIC_PATHS)
        auto mode = (export_counter == 0 ? std::ios::out : std::ios::app);
        std::ofstream f(MTS_DEBUG_ACOUSTIC_PATHS, mode);
        typedef std::array<float, 3> Point;
        typedef std::pair<Point, Point> Line;
        typedef std::vector<Line> Path;
        
        std::vector<Path> paths;

        if constexpr (is_cuda_array_v<Float> || is_diff_array_v<Float>) {
            for (size_t i = 0; i < band_id.size(); i++) {
                Path p;
                paths.push_back(p);
            }

        } else {
            f << "o path" << path_counter++ << std::endl;
        }
        
#endif

        Ray3f ray = ray_;

        Float distance = 0.f;
        const ScalarFloat discretizer = MTS_SOUND_SPEED * m_max_time;

        // MIS weight for intersected emitters (set by prev. iteration)
        Float emission_weight(1.f);

        Spectrum throughput(1.f);

        // ---------------------- First intersection ----------------------

        SurfaceInteraction3f si = scene->ray_intersect(ray, active);
        Mask valid_ray          = si.is_valid();
        EmitterPtr emitter      = si.emitter(scene);

        Mask hit_emitter_before = false;

        for (int depth = 1;; ++depth) {

            // std::cout << "depth: " << depth << std::endl;
            // std::cout << "throughput: " << throughput[0] << std::endl;
            // std::cout << "emission_weight: " << emission_weight << std::endl;
            // std::cout << "distance: " << distance << std::endl;
            // std::cout << "any(isnan(ray.d)): " << any(isnan(ray.d)) << std::endl;

            // ScalarFloat total_rays = count(active) + count(!active);

            // std::cout << "depth: " << depth << std::endl;
            // std::cout << "avg throughput: " << hsum(throughput[0]) / count(active) << std::endl;
            // std::cout << "%(any(isnan(ray.d))): " << count(any(isnan(ray.d))) / total_rays << std::endl;
            // std::cout << "%(active): " << count(active) / total_rays << std::endl;
            // std::cout << "count(any(isnan(ray.d)) && active): " << count(any(isnan(ray.d)) && active) << std::endl;

            
#if defined(MTS_DEBUG_ACOUSTIC_PATHS)
            // if(count(any(isnan(ray.d))) > 0) {
            //     break;
            // }

            if constexpr (is_cuda_array_v<Float> || is_diff_array_v<Float>) {

                for (size_t n = 0; n < band_id.size(); n++) {
                    size_t s = n;

                    auto origin = ray.o;
                    auto target = si.p;

                    if (origin.x().size() == 1) {
                        s = 0;
                    }

                    Point a = { origin.x()[s], origin.y()[s], origin.z()[s] };
                    Point b = { target.x()[s], target.y()[s], target.z()[s] };
                    Line l = { a, b };
                    paths.at(n).push_back(l);
                }
            } else {
                size_t i  = 0;

                auto origin = ray.o;
                auto target = si.p;

                f << "v " << origin.x() << " " << origin.y() << " " << origin.z() << std::endl;
                f << "v " << target.x() << " " << target.y() << " " << target.z() << std::endl;
                i += 2;

                f << "l";
                for (size_t j = 1; j <= i; ++j)
                    f << " " << (export_counter + j);
                f << std::endl;
                export_counter += i;
            }
#endif

           // Update traveled distance
           distance += si.t;

           Mask hit_emitter = neq(emitter, nullptr);

            // ---------------- Intersection with sensors ----------------
            if (any_or<true>(hit_emitter)) {

                //std::cout << "count(hit_emitter) = " << count(hit_emitter) << std::endl;

                // Logging the result
                Float time_frac = (distance / discretizer) * hist->size().x();

                Mask valid_hit = hit_emitter && !hit_emitter_before;

                //hist->put({ time_frac, band_id }, emission_weight * throughput * emitter->eval(si, hit_emitter), hit_emitter);
                hist->put({ time_frac, band_id }, emission_weight * throughput, valid_hit);

                hit_emitter_before = hit_emitter;

            }
            active &= si.is_valid();

            // Stop if we've exceeded the number of requested bounces, or
            // if there are no more active lanes. Only do this latter check
            // in GPU mode when the number of requested bounces is infinite
            // since it causes a costly synchronization.
            if ((uint32_t) depth >= (uint32_t) m_max_depth ||
                ((!is_cuda_array_v<Float> || m_max_depth < 0) && none(active)))
                break;

            // --------------------- Emitter sampling ---------------------

            BSDFContext ctx;
            BSDFPtr bsdf = si.bsdf(ray);
            Mask active_e = active && has_flag(bsdf->flags(), BSDFFlags::DiffuseReflection);

            if (likely(any_or<true>(active_e))) {
                auto [ds, emitter_val] = scene->sample_emitter_direction(
                    si, sampler->next_2d(active_e), true, active_e);
                active_e &= neq(ds.pdf, 0.f);

                // Query the BSDF for that emitter-sampled direction
                Vector3f wo = si.to_local(ds.d);
                Spectrum bsdf_val = bsdf->eval(ctx, si, wo, active_e);

                // Determine density of sampling that same direction using BSDF sampling
                Float bsdf_pdf = bsdf->pdf(ctx, si, wo, active_e);

                Float mis = select(ds.delta, 1.f, mis_weight(ds.pdf, bsdf_pdf));

                Spectrum expected_throughput = throughput * bsdf_val * mis; // * mis * emitter_val;

                // std::cout << "throughput: " << throughput[0] << std::endl;
                // std::cout << "expected_throughput: " << expected_throughput[0] << std::endl;
                // std::cout << "bsdf_val: " << bsdf_val[0] << std::endl;
                

                // Logging the result
                Float time_frac = ((distance + ds.dist) / discretizer) * hist->size().x();
                // std::cout << "time_frac: " << time_frac << std::endl;
                hist->put({ time_frac, band_id }, expected_throughput, active_e);

            }

            // ----------------------- BSDF sampling ----------------------

            // Sample BSDF * cos(theta)
            auto [bs, bsdf_val] = bsdf->sample(ctx, si, sampler->next_1d(active),
                                               sampler->next_2d(active), active);


            // std::cout << "bsdf_val[0]: " << bsdf_val[0] << std::endl;
            //std::cout << "avg bsdf_val: " << hsum(bsdf_val[0]) / count(active) << std::endl;

            throughput = throughput * bsdf_val;
            active &= any(neq(throughput, 0.f));
            if (none_or<false>(active))
                break;

            // Intersect the BSDF ray against the scene geometry
            ray = si.spawn_ray(si.to_world(bs.wo));
            SurfaceInteraction3f si_bsdf = scene->ray_intersect(ray, active);

            emitter = si_bsdf.emitter(scene, active);

            /* Determine probability of having sampled that same
               direction using emitter sampling. */
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
#if defined(MTS_DEBUG_ACOUSTIC_PATHS)
            if constexpr (is_cuda_array_v<Float> || is_diff_array_v<Float>) {

                if (count(any(isnan(ray.d)) && active) > 0) {
                    Mask active_and_nan_d = any(isnan(ray.d) && active);
                }
                for (auto p : paths) {
                    f << "o path" << path_counter++ << std::endl;
                    size_t d = 0;

                    for (auto l : p) {
                        size_t i  = 0;
                        f << "g depth" << d++ << std::endl;

                        f << "v " << l.first[0] << " " << l.first[1] << " " << l.first[2] << std::endl;
                        f << "v " << l.second[0] << " " << l.second[1] << " " << l.second[2] << std::endl;
                        i += 2;

                        f << "l";
                        for (size_t j = 1; j <= i; ++j)
                            f << " " << (export_counter + j);
                        f << std::endl;
                        export_counter += i;
                    }
                }
            }
#endif


        return { throughput, valid_ray };
    }

    //! @}
    // =============================================================

    std::string to_string() const override {
        std::ostringstream oss;
        oss << "AcousticPathIntegrator[" << std::endl
            << "  stop = " << m_stop << "," << std::endl
            << "  max_depth = " << m_max_depth << "," << std::endl
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
