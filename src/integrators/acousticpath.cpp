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
    MTS_IMPORT_BASE(TimeDependentIntegrator, m_stop, m_max_depth, m_rr_depth,
                    m_max_time, m_time_steps, m_wavelength_bins)
    MTS_IMPORT_TYPES(Scene, Sensor, Sampler, Medium, Emitter, EmitterPtr, BSDF,
                     BSDFPtr)

    AcousticPathIntegrator(const Properties &props) : Base(props) {}

    std::pair<Spectrum, Mask> sample(const Scene *scene, Sampler *sampler,
                                     const RayDifferential3f &ray_,
                                     const Medium * /* medium */,
                                     Float * /* aovs */,
                                     Mask active) const override {
        MTS_MASKED_FUNCTION(ProfilerPhase::SamplingIntegratorSample, active);

        RayDifferential3f ray = ray_;

        // MIS weight for intersected emitters (set by prev. iteration)
        Float emission_weight(1.f);

        Spectrum throughput(1.f), result(0.f);

        // ---------------------- First intersection ----------------------

        SurfaceInteraction3f si = scene->ray_intersect(ray, active);
        Mask valid_ray          = si.is_valid();
        EmitterPtr emitter      = si.emitter(scene);

        for (int depth = 1;; ++depth) {

            // ---------------- Intersection with emitters ----------------

            if (any_or<true>(neq(emitter, nullptr)))
                result[active] +=
                    emission_weight * throughput * emitter->eval(si, active);

            active &= si.is_valid();

            // Stop if we've exceeded the number of requested bounces, or
            // if there are no more active lanes. Only do this latter check
            // in GPU mode when the number of requested bounces is infinite
            // since it causes a costly synchronization.
            if ((uint32_t) depth >= (uint32_t) m_max_depth ||
                ((!is_cuda_array_v<Float> || m_max_depth < 0) && none(active)))
                break;
        }

        return { result, valid_ray };
    }

    //! @}
    // =============================================================

    std::string to_string() const override {
        std::ostringstream oss;
        oss << "AcousticPathIntegrator[" << std::endl
            << "  stop = " << m_stop << "," << std::endl
            << "  max_depth = " << m_max_depth << "," << std::endl
            << "  rr_depth = " << m_rr_depth << "," << std::endl
            << "  max_time = " << m_max_time << "," << std::endl
            << "  time_steps = " << m_time_steps << "," << std::endl
            << "  wavelength_bins = " << m_wavelength_bins;
        oss << std::endl << "]";
        return oss.str();
    }

    MTS_DECLARE_CLASS()
};

MTS_IMPLEMENT_CLASS_VARIANT(AcousticPathIntegrator, TimeDependentIntegrator)
MTS_EXPORT_PLUGIN(AcousticPathIntegrator, "Acoustic Path Tracer integrator");
NAMESPACE_END(mitsuba)
