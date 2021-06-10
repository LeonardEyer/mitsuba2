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
    }

    ~Microphone() {}

    std::pair<Ray3f, Spectrum> sample_ray(Float time, Float wavelength_sample,
                                          const Point2f & /*sample2*/,
                                          const Point2f &sample3,
                                          Mask active) const override {

        MTS_MASKED_FUNCTION(ProfilerPhase::EndpointSampleRay, active);

        // 0. Get transform
        auto transform = m_world_transform->eval(time, active);

        // 1. Get translation
        auto origin = transform.translation();

        // 2. Sample directional component
        Vector3f direction = warp::square_to_uniform_sphere(sample3);

        // All wavelengths are equally weighted
        Spectrum wav_weight = 1.f;

        return { Ray3f(origin, direction, time, wavelength_sample),
                 unpolarized<Spectrum>(wav_weight) * math::Pi<ScalarFloat> };
    }


    std::pair<RayDifferential3f, Spectrum> sample_ray_differential(Float time, Float wavelength_sample,
                                          const Point2f & /*sample2*/,
                                          const Point2f &sample3,
                                          Mask active) const override {

        MTS_MASKED_FUNCTION(ProfilerPhase::EndpointSampleRay, active);

        // 0. Get transform
        auto transform = m_world_transform->eval(time, active);

        // 1. Get translation
        auto origin = transform.translation();

        // 2. Sample directional component
        Vector3f direction = warp::square_to_uniform_sphere(sample3);

        // All wavelengths are equally weighted
        Spectrum wav_weight = 1.f;

        RayDifferential3f ray;
        ray.time = time;
        ray.wavelengths = wavelength_sample;
        ray.mint = math::RayEpsilon<Float>;
        ray.maxt = math::Infinity<Float>;

        ray.o = origin;
        ray.d = direction;
        ray.update();

        ray.o_x = ray.o_y = ray.o;
        ray.d_x = ray.d_y = ray.d;
        ray.scale_differential(Float(0.03f));
        ray.has_differentials = true;

        return { ray,
                 unpolarized<Spectrum>(wav_weight) * math::Pi<ScalarFloat> };
    }

    ScalarBoundingBox3f bbox() const override {
        // Return an invalid bounding box
        return ScalarBoundingBox3f();
    }

    void traverse(TraversalCallback *callback) override {
        Base::traverse(callback);
    }

    std::string to_string() const override {
        std::ostringstream oss;
        oss << "Microphone[" << std::endl
            //<< "  wavelengths = " << m_wavelengths << "," << std::endl
            << "]";
        return oss.str();
    }

    MTS_DECLARE_CLASS()
private:

};

MTS_IMPLEMENT_CLASS_VARIANT(Microphone, Sensor)
MTS_EXPORT_PLUGIN(Microphone, "Microphone");
NAMESPACE_END(mitsuba)