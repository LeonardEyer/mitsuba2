#include <mitsuba/render/texture.h>
#include <mitsuba/render/interaction.h>
#include <mitsuba/core/properties.h>
#include <mitsuba/core/distr_1d.h>

NAMESPACE_BEGIN(mitsuba)

const float data[10] = {
    10.88f, 5.44f, 2.74f, 1.37f, 0.68f, 0.343f, 0.172f, 0.086f, 0.043f, 0.021f
};

/**!

.. _spectrum-audible:

Audible spectrum
------------------------------------

This spectrum returns the audible frequency range spectrum from 20 to 20.000 Hz
 -> ~17mm to 17m

 */

template <typename Float, typename Spectrum>
class AudibleSpectrum final : public Texture<Float, Spectrum> {
public:
    MTS_IMPORT_TYPES(Texture)

    explicit AudibleSpectrum(const Properties &props) : Texture(props) {
    }

    std::vector<ref<Object>> expand() const override {
        // This plugin recursively expands into an instance of 'interpolated'
        Properties props("irregular");
        props.set_float("lambda_min", 0.0175);
        props.set_float("lambda_max", 17.0);
        props.set_int("size", 10);
        ScalarFloat tmp[10];
        for (size_t i = 0; i < 10; ++i)
            tmp[i] = data[9-i];
        props.set_pointer("values", (const void *) &tmp[0]);

        PluginManager *pmgr = PluginManager::instance();
        return { ref<Object>(pmgr->create_object<Texture>(props)) };
    }

    std::string to_string() const override {
        std::ostringstream oss;
        oss << "AudibleSpectrum[" << std::endl
            << "  n/a = " << "n/a" << std::endl
            << "]";
        return oss.str();
    }
    
    MTS_DECLARE_CLASS()
};

MTS_IMPLEMENT_CLASS_VARIANT(AudibleSpectrum, Texture)
MTS_EXPORT_PLUGIN(AudibleSpectrum, "Audible spectrum")
NAMESPACE_END(mitsuba)
