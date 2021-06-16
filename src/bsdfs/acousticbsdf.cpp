#include <mitsuba/core/properties.h>
#include <mitsuba/core/spectrum.h>
#include <mitsuba/core/warp.h>
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

        m_flags = BSDFFlags::DeltaReflection | BSDFFlags::DiffuseReflection | BSDFFlags::FrontSide;
        m_components.push_back(m_flags);
    }

    std::pair<BSDFSample3f, Spectrum> sample(const BSDFContext &/*ctx*/,
                                             const SurfaceInteraction3f &si,
                                             Float sample1,
                                             const Point2f &sample2,
                                             Mask active) const override {
        MTS_MASKED_FUNCTION(ProfilerPhase::BSDFSample, active);

        Float cos_theta_i = Frame3f::cos_theta(si.wi);
        active &= cos_theta_i > 0.f;

        //std::cout << "cos_theta_i" << cos_theta_i << std::endl;

        Float scatter = clamp(m_scatter->eval_1(si, active), 0.f, 1.f);

        Mask m0 = active && sample1 >  scatter,
             m1 = active && sample1 <= scatter;

        auto bs = zero<BSDFSample3f>();
        Spectrum result(0.f);

        UnpolarizedSpectrum reflectance = 1.f - m_absorpt->eval(si, active);

        //std::cout << "m0" << m0 << std::endl;
        //std::cout << "m1" << m1 << std::endl;
        //std::cout << "scatter" << scatter << std::endl;
        //std::cout << "reflectance" << reflectance << std::endl;

        if (any_or<true>(m0)) {
            // Specular component
            auto bs_specular = zero<BSDFSample3f>();

            bs_specular.sampled_component = 0;
            bs_specular.sampled_type = +BSDFFlags::DeltaReflection;
            bs_specular.wo  = reflect(si.wi);
            bs_specular.eta = 1.f;
            bs_specular.pdf = 1.f;

            masked(bs, m0) = bs_specular;
            masked(result, m0) = reflectance * (1.f - scatter);
        }

        if (any_or<true>(m1)) {
            // Diffuse component
            auto bs_diffuse = zero<BSDFSample3f>();

            bs_diffuse.wo = warp::square_to_cosine_hemisphere(sample2);
            bs_diffuse.pdf = warp::square_to_cosine_hemisphere_pdf(bs_diffuse.wo);
            bs_diffuse.eta = 1.f;
            bs_diffuse.sampled_type = +BSDFFlags::DiffuseReflection;
            bs_diffuse.sampled_component = 0;

            masked(bs, m1) = bs_diffuse;
            masked(result, m1) = reflectance * scatter;

        }

        return { bs, result & active };
    }

    Spectrum eval(const BSDFContext &/* ctx */, const SurfaceInteraction3f &si,
                  const Vector3f &wo, Mask active) const override {
        MTS_MASKED_FUNCTION(ProfilerPhase::BSDFEvaluate, active);

        Float cos_theta_i = Frame3f::cos_theta(si.wi),
              cos_theta_o = Frame3f::cos_theta(wo);

        active &= cos_theta_i > 0.f && cos_theta_o > 0.f;

        Float scatter = clamp(m_scatter->eval_1(si, active), 0.f, 1.f);

        UnpolarizedSpectrum reflectance = 1.f - m_absorpt->eval(si, active);

        UnpolarizedSpectrum value_specular = reflectance * select(reflect(si.wi) == wo, 1.f, 0.f);
        UnpolarizedSpectrum value_diffuse = reflectance * math::InvPi<Float> * cos_theta_o;

        //std::cout << "scatter" << scatter << std::endl;
        //std::cout << "(value_specular * (1.f - scatter)) + (value_diffuse * scatter)" << (value_specular * (1.f - scatter)) + (value_diffuse * scatter) << std::endl;
        //std::cout << "bsdf:count(active)" << count(active) << std::endl;
        ////std::cout << "reflectance" << reflectance << std::endl;

        return select(active,
                      (value_specular * (1.f - scatter)) + (value_diffuse * scatter),
                      0.f);
    }

    Float pdf(const BSDFContext &/* ctx */, const SurfaceInteraction3f & si,
              const Vector3f &wo, Mask active) const override {

        MTS_MASKED_FUNCTION(ProfilerPhase::BSDFEvaluate, active);

        Float cos_theta_i = Frame3f::cos_theta(si.wi),
              cos_theta_o = Frame3f::cos_theta(wo);

        active &= cos_theta_i > 0.f && cos_theta_o > 0.f;

        Float scatter = clamp(m_scatter->eval_1(si, active), 0.f, 1.f);

        Float pdf_specular = (select(reflect(si.wi) == wo, 1.f, 0.f));
        Float pdf_diffuse = warp::square_to_cosine_hemisphere_pdf(wo);

        return select(active,
                      (pdf_specular * (1.f - scatter)) +
                         (pdf_diffuse * scatter),
                      0.f);
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