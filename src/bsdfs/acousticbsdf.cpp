
#include <mitsuba/core/properties.h>
#include <mitsuba/core/spectrum.h>
#include <mitsuba/core/string.h>
#include <mitsuba/render/bsdf.h>
#include <mitsuba/render/texture.h>

NAMESPACE_BEGIN(mitsuba)

template <typename Float, typename Spectrum>
class AcousticBSDF final : public BSDF<Float, Spectrum>{
public :
    MTS_IMPORT_BASE(BSDF, m_flags, m_components)
    MTS_IMPORT_TYPES(Texture)

    AcousticBSDF(const Properties &props): Base(props) {
        m_scatter = props.texture<Texture>("scattering");
        m_absorpt = props.texture<Texture>("absorption");

        m_flags = BSDFFlags::DeltaReflection | BSDFFlags::FrontSide;
        m_components.push_back(m_flags);
    }

    std::pair<BSDFSample3f, Spectrum> sample(const BSDFContext &ctx,
                                             const SurfaceInteraction3f &si,
                                             Float sample1,
                                             const Point2f &sample2,
                                             Mask active) const override {
        MTS_MASKED_FUNCTION(ProfilerPhase::BSDFSample, active);

        Float cos_theta_i = Frame3f::cos_theta(si.wi);
        active &= cos_theta_i > 0.f;

        auto bs = zero<BSDFSample3f>();

        bs.sampled_component = 0;
        bs.sampled_type = +BSDFFlags::DeltaReflection;
        bs.wo  = reflect(si.wi);
        bs.eta = 1.f;
        bs.pdf = 1.f;

        UnpolarizedSpectrum reflectance = 1.f - m_absorpt->eval(si, active);

        return { bs, reflectance & active };
    }

    Spectrum eval(const BSDFContext &ctx, const SurfaceInteraction3f &si,
                  const Vector3f &wo, Mask active) const override {

        return 0.f;
    }

    Float pdf(const BSDFContext &ctx, const SurfaceInteraction3f &si,
              const Vector3f &wo, Mask active) const override {
        return 0.f;
    }

    void traverse(TraversalCallback *callback) override {
        callback->put_object("scattering", m_scatter.get());
        callback->put_object("absorption", m_absorpt.get());
    }

    std::string to_string() const override {
        std::ostringstream oss;
        oss << "AcousticBSDF[" << std::endl
            << "  scattering = " << string::indent(m_scatter) << "," << std::endl
            << "  absorption = " << string::indent(m_absorpt) << "," << std::endl
            << "]";
        return oss.str();
    }


    MTS_DECLARE_CLASS()
protected:
    ref<Texture> m_scatter;
    ref<Texture> m_absorpt;
};

MTS_IMPLEMENT_CLASS_VARIANT(AcousticBSDF, BSDF)
MTS_EXPORT_PLUGIN(AcousticBSDF, "AcousticBSDF material")
NAMESPACE_END(mitsuba)