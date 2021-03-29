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
    MTS_IMPORT_BASE(Sensor, m_world_transform)
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
    }

    std::pair<RayDifferential3f, Spectrum>
    sample_ray_differential(Float time, Float wavelength_sample,
                            const Point2f &/*sample2*/, const Point2f &sample3,
                            Mask active) const override {

        MTS_MASKED_FUNCTION(ProfilerPhase::EndpointSampleRay, active);

        // 0. Get transform
        auto transform = m_world_transform->eval(time, active);

        // 1. Get translation
        auto origin = transform.translation();

        // 2. Sample directional component
        Vector3f direction = warp::square_to_uniform_sphere(sample3);

        // 3. Sample spectrum
        UInt32 index = enoki::ceil(wavelength_sample * (m_wavelengths.size() - 1));
        Wavelength wavelengths = gather<Float>(m_wavelengths, index, active);

        // All wavelengths are equally weighted
        Spectrum wav_weight = 1.f;

        Ray3f ray;
        ray.time = time;
        ray.o = origin;
        ray.d = direction;
        ray.wavelengths = wavelengths;

        return {
            ray,
            unpolarized<Spectrum>(wav_weight) * math::Pi<ScalarFloat>
        };
    }

    ScalarBoundingBox3f bbox() const override {
        // Return an invalid bounding box
        return ScalarBoundingBox3f();
    }

    std::string to_string() const override {
        std::ostringstream oss;
        oss << "Microphone[" << std::endl
            << "  wavelengths = " << m_wavelengths << "," << std::endl
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