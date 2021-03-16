//
// Created by Leonard Eyer on 21.12.20.
//
#include <mitsuba/core/fwd.h>
#include <mitsuba/core/properties.h>
#include <mitsuba/core/transform.h>
#include <mitsuba/core/warp.h>
#include <mitsuba/render/fwd.h>
#include <mitsuba/render/sensor.h>
#include <mitsuba/render/texture.h>

NAMESPACE_BEGIN(mitsuba)

MTS_VARIANT class Microphone final : public Sensor<Float, Spectrum> {
public:
    MTS_IMPORT_BASE(Sensor, m_world_transform, m_shape)
    MTS_IMPORT_TYPES(Shape, Texture)

    Microphone(const Properties &props) : Base(props) {
        std::vector<std::string> wavelengths_str =
                string::tokenize(props.string("wavelengths"), " ,");

        // Allocate space
        m_wavelengths = zero<DynamicBuffer<Float>>(wavelengths_str.size());

        // Copy and convert to wavelengths
        for (size_t i = 0; i < wavelengths_str.size(); ++i) {
            try {
                Float wav = std::stod(wavelengths_str[i]);
                scatter(m_wavelengths, wav, UInt32(i));
            } catch (...) {
                Throw("Could not parse floating point value '%s'",
                      wavelengths_str[i]);
            }
        }

        if (props.has_property("to_world"))
            Throw("Found a 'to_world' transformation -- this is not allowed. "
                  "The irradiance meter inherits this transformation from its "
                  "parent "
                  "shape.");
    }

    std::pair<RayDifferential3f, Spectrum>
    sample_ray_differential(Float time, Float wavelength_sample,
                            const Point2f &sample2, const Point2f &sample3,
                            Mask active) const override {

        MTS_MASKED_FUNCTION(ProfilerPhase::EndpointSampleRay, active);

        // 1. Sample spatial component
        PositionSample3f ps = m_shape->sample_position(time, sample2, active);

        // 2. Sample directional component
        Vector3f local = warp::square_to_cosine_hemisphere(sample3);

        UInt32 index = enoki::ceil(wavelength_sample * (m_wavelengths.size() - 1));

        // 3. Sample spectrum
        Wavelength wavelengths = gather<Float>(m_wavelengths, index, active);
        Spectrum wav_weight = 1.f;

        return std::make_pair(
            RayDifferential3f(ps.p, Frame3f(ps.n).to_world(local), time,
                              wavelengths),
            unpolarized<Spectrum>(wav_weight) * math::Pi<ScalarFloat>);
    }

    std::pair<DirectionSample3f, Spectrum>
    sample_direction(const Interaction3f &it, const Point2f &sample,
                     Mask active) const override {
        return std::make_pair(m_shape->sample_direction(it, sample, active),
                              math::Pi<ScalarFloat>);
    }

    Float pdf_direction(const Interaction3f &it, const DirectionSample3f &ds,
                        Mask active) const override {
        return m_shape->pdf_direction(it, ds, active);
    }

    Spectrum eval(const SurfaceInteraction3f & /*si*/,
                  Mask /*active*/) const override {
        return math::Pi<ScalarFloat> / m_shape->surface_area();
    }

    ScalarBoundingBox3f bbox() const override { return m_shape->bbox(); }

    std::string to_string() const override {
        std::ostringstream oss;
        oss << "Microphone[" << std::endl
            << "  shape = " << m_shape << "," << std::endl
            //<< "  wavelengths = " << m_wavelengths << "," << std::endl
            << "]";
        return oss.str();
    }

    MTS_DECLARE_CLASS()
private:
    DynamicBuffer<Float> m_wavelengths;
};

MTS_IMPLEMENT_CLASS_VARIANT(Microphone, Sensor)
MTS_EXPORT_PLUGIN(Microphone, "Microphone");
NAMESPACE_END(mitsuba)