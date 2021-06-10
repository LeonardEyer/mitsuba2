#include <mitsuba/core/properties.h>
#include <mitsuba/core/warp.h>
#include <mitsuba/core/spectrum.h>
#include <mitsuba/render/emitter.h>
#include <mitsuba/render/medium.h>
#include <mitsuba/render/shape.h>
#include <mitsuba/render/texture.h>

NAMESPACE_BEGIN(mitsuba)

template <typename Float, typename Spectrum>
class SmoothSphereEmitter final : public Emitter<Float, Spectrum> {
public:
    MTS_IMPORT_BASE(Emitter, m_flags, m_shape, m_medium)
    MTS_IMPORT_TYPES(Scene, Shape, Texture)

    SmoothSphereEmitter(const Properties &props) : Base(props) {
        if (props.has_property("to_world"))
            Throw("Found a 'to_world' transformation -- this is not allowed. "
                  "The area light inherits this transformation from its parent "
                  "shape.");

        m_radiance = props.texture<Texture>("radiance", Texture::D65(1.f));
        m_blur_size = props.float_("blur_size", 0.1f);

        // TODO: detect if underlying spectrum really is spatially varying
        m_flags = EmitterFlags::Surface | EmitterFlags::SpatiallyVarying;
    }

    void set_shape(Shape *shape) override {
        if (m_shape)
            Throw("An area emitter can be only be attached to a single shape.");

        Base::set_shape(shape);
        m_area_times_pi = m_shape->surface_area() * math::Pi<ScalarFloat>;
    }

    Float smooth_profile(Float x) const {
        //x = abs(x);
        Float res(0);
        res = select(x >= m_blur_size, Float(1), res);
        res = select(x < m_blur_size, x / m_blur_size, res);
        return res;
    }

    Spectrum eval(const SurfaceInteraction3f &si, Mask active) const override {
        MTS_MASKED_FUNCTION(ProfilerPhase::EndpointEvaluate, active);

        //Float r = Float(1) - (pow(si.wi.x(), 2) + pow(si.wi.y(), 2));
        // std::cout << "r; " << r << std::endl;

        // auto world_si_frame = Frame3f(si.sh_frame.to_world(si.wi));
        // auto local_p = world_si_frame.to_local(si.n);
        // Float r2 = Float(1) - (pow(local_p.x(), 2) + pow(local_p.y(), 2));
        // std::cout << "r2; " << r2 << std::endl;

        Float x = Frame3f::cos_theta(si.wi);



        return select(
            Frame3f::cos_theta(si.wi) > 0.f,
            unpolarized<Spectrum>(m_radiance->eval(si, active)) * smooth_profile(0.5f - (acos(x) / math::Pi<ScalarFloat>)),
            0.f
        );
    }

    std::pair<Ray3f, Spectrum> sample_ray(Float time, Float wavelength_sample,
                                          const Point2f &sample2, const Point2f &sample3,
                                          Mask active) const override {
        MTS_MASKED_FUNCTION(ProfilerPhase::EndpointSampleRay, active);
        std::cout << "sample_ray" << std::endl;

        // 1. Sample spatial component
        PositionSample3f ps = m_shape->sample_position(time, sample2, active);

        // 2. Sample directional component
        Vector3f local = warp::square_to_cosine_hemisphere(sample3);

        // 3. Sample spectrum
        SurfaceInteraction3f si(ps, zero<Wavelength>(0.f));
        auto [wavelengths, spec_weight] = m_radiance->sample(
            si, math::sample_shifted<Wavelength>(wavelength_sample), active);

        //Float r = Float(1) - (pow(local.x(), 2) + pow(local.y(), 2));

        //spec_weight *= smooth_profile(r);

        return std::make_pair(
            Ray3f(ps.p, Frame3f(ps.n).to_world(local), time, wavelengths),
            unpolarized<Spectrum>(spec_weight) * m_area_times_pi
        );
    }

    std::pair<DirectionSample3f, Spectrum>
    sample_direction(const Interaction3f &it, const Point2f &sample, Mask active) const override {
        MTS_MASKED_FUNCTION(ProfilerPhase::EndpointSampleDirection, active);

        Assert(m_shape, "Can't sample from an area emitter without an associated Shape.");

        DirectionSample3f ds = m_shape->sample_direction(it, sample, active);
        active &= dot(ds.d, ds.n) < 0.f && neq(ds.pdf, 0.f);

        SurfaceInteraction3f si(ds, it.wavelengths);
        Spectrum spec = m_radiance->eval(si, active) / ds.pdf;

        // Float r = Float(1) - (pow(ds.n.x(), 2) + pow(ds.n.y(), 2));
        // spec *= smooth_profile(r);

        ds.object = this;
        return { ds, unpolarized<Spectrum>(spec) & active };
    }

    Float pdf_direction(const Interaction3f &it, const DirectionSample3f &ds,
                        Mask active) const override {
        MTS_MASKED_FUNCTION(ProfilerPhase::EndpointEvaluate, active);

        return select(dot(ds.d, ds.n) < 0.f,
                      m_shape->pdf_direction(it, ds, active), 0.f);
    }

    ScalarBoundingBox3f bbox() const override { return m_shape->bbox(); }

    void traverse(TraversalCallback *callback) override {
        callback->put_object("radiance", m_radiance.get());
    }

    void parameters_changed(const std::vector<std::string> &keys) override {
        if (string::contains(keys, "parent"))
            m_area_times_pi = m_shape->surface_area() * math::Pi<ScalarFloat>;
    }

    std::string to_string() const override {
        std::ostringstream oss;
        oss << "SmoothSphereEmitter[" << std::endl
            << "  radiance = " << string::indent(m_radiance) << "," << std::endl
            << "  blur_size = " << m_blur_size << "," << std::endl
            << "  surface_area = ";
        if (m_shape) oss << m_shape->surface_area();
        else         oss << "  <no shape attached!>";
        oss << "," << std::endl;
        if (m_medium) oss << string::indent(m_medium->to_string());
        else         oss << "  <no medium attached!>";
        oss << std::endl << "]";
        return oss.str();
    }

    MTS_DECLARE_CLASS()
private:
    ref<Texture> m_radiance;
    ScalarFloat m_area_times_pi = 0.f;
    ScalarFloat m_blur_size;
};

MTS_IMPLEMENT_CLASS_VARIANT(SmoothSphereEmitter, Emitter)
MTS_EXPORT_PLUGIN(SmoothSphereEmitter, "Smooth Sphere emitter")
NAMESPACE_END(mitsuba)

