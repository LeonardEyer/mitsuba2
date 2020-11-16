#include <random>
#include <enoki/stl.h>
#include <mitsuba/core/ray.h>
#include <mitsuba/core/properties.h>
#include <mitsuba/render/bsdf.h>
#include <mitsuba/render/emitter.h>
#include <mitsuba/render/integrator.h>
#include <mitsuba/render/records.h>

NAMESPACE_BEGIN(mitsuba)

template <typename Float, typename Spectrum>
class AcousticPathIntegrator : public TimeDependentIntegrator<Float, Spectrum> {
public:
    MTS_IMPORT_BASE(TimeDependentIntegrator, m_max_time)
    MTS_IMPORT_TYPES(Scene, Sampler, Medium, Emitter, EmitterPtr, BSDF, BSDFPtr)

    AcousticPathIntegrator(const Properties &props) : Base(props) { }

    std::pair<Spectrum, Mask> sample(const Scene *scene,
                                     Sampler *sampler,
                                     const RayDifferential3f &ray_,
                                     const Medium * /* medium */,
                                     Float * /* aovs */,
                                     Mask active) const {
        MTS_MASKED_FUNCTION(ProfilerPhase::SamplingIntegratorSample, active);

        Throw("\"sample\" not implemented");
    }

    //! @}
    // =============================================================

    std::string to_string() const override {
        return tfm::format("AcousticPathIntegrator[\n"
                           "  max_time = %i,\n"
                           "]", m_max_time);
    }

    MTS_DECLARE_CLASS()
};

MTS_IMPLEMENT_CLASS_VARIANT(AcousticPathIntegrator, TimeDependentIntegrator)
MTS_EXPORT_PLUGIN(AcousticPathIntegrator, "Acoustic Path Tracer integrator");
NAMESPACE_END(mitsuba)
