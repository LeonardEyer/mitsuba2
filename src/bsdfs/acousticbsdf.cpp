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

        PluginManager *pmgr = PluginManager::instance();

        Properties propsDiffuse("diffuse");
        Properties propsConduct("conductor");

        // Copy absorption coefficients
        // (conversion is handled in spectra/acoustic.cpp)
        propsDiffuse.set_object("reflectance", m_absorpt);

        ref<Base> diffuser = pmgr->create_object<Base>(propsDiffuse);
        ref<Base> conductor = pmgr->create_object<Base>(propsConduct);

        Properties propsBlend("blendbsdf");
        // Weighting
        propsBlend.set_object("weight", m_scatter);
        // Nested bsdfs
        propsBlend.set_object("0_conductor", conductor);
        propsBlend.set_object("1_diffuser", diffuser);

        m_nested_bsdf = pmgr->create_object<Base>(propsBlend);
    }

    std::pair<BSDFSample3f, Spectrum> sample(const BSDFContext &ctx,
                                             const SurfaceInteraction3f &si,
                                             Float sample1,
                                             const Point2f &sample2,
                                             Mask active) const override {
        return m_nested_bsdf->sample(ctx, si, sample1, sample2, active);
    }

    Spectrum eval(const BSDFContext &ctx, const SurfaceInteraction3f &si,
                  const Vector3f &wo, Mask active) const override {
        return m_nested_bsdf->eval(ctx, si, wo, active);
    }

    Float pdf(const BSDFContext &ctx, const SurfaceInteraction3f &si,
              const Vector3f &wo, Mask active) const override {
        return m_nested_bsdf->pdf(ctx, si, wo, active);
    }

    void traverse(TraversalCallback *callback) override {
        return m_nested_bsdf->traverse(callback);
    }

    std::string to_string() const override {
        std::ostringstream oss;
        oss << "AcousticBSDF[" << std::endl
            << "  scattering = " << string::indent(m_scatter) << "," << std::endl
            << "  absorption = " << string::indent(m_absorpt) << "," << std::endl
            << "  nested_bsdf = " << string::indent(m_nested_bsdf) << std::endl
            << "]";
        return oss.str();
    }


    MTS_DECLARE_CLASS()
protected:
    ref<Texture> m_scatter;
    ref<Texture> m_absorpt;
    ref<Base> m_nested_bsdf;
};

MTS_IMPLEMENT_CLASS_VARIANT(AcousticBSDF, BSDF)
MTS_EXPORT_PLUGIN(AcousticBSDF, "AcousticBSDF material")
NAMESPACE_END(mitsuba)