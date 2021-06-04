#include <mitsuba/core/distr_1d.h>
#include <mitsuba/core/properties.h>
#include <mitsuba/render/interaction.h>
#include <mitsuba/render/texture.h>
#include <numeric>

NAMESPACE_BEGIN(mitsuba)

enum bands { low, center, high, all };

/**!

.. _spectrum-audible:

Audible spectrum
------------------------------------

This spectrum returns reflectance or emission values from the audible frequency
range (20 to 20.000 Hz -> ~17mm to 17m).

 */
template <typename Float, typename Spectrum>
class AcousticSpectrum final : public Texture<Float, Spectrum> {
public:
    MTS_IMPORT_TYPES(Texture)

    AcousticSpectrum(const Properties &props)
        : Texture(props), m_lambda_min(MTS_AUDIBLE_WAVELENGTH_MIN),
          m_lambda_max(MTS_AUDIBLE_WAVELENGTH_MAX) {

        if (props.has_property("lambda_min"))
            m_lambda_min =
                max(props.float_("lambda_min"), MTS_AUDIBLE_WAVELENGTH_MIN);

        if (props.has_property("lambda_max"))
            m_lambda_max =
                min(props.float_("lambda_max"), MTS_AUDIBLE_WAVELENGTH_MAX);

        if (props.has_property("freq_min"))
            m_lambda_max = max(MTS_SOUND_SPEED / props.float_("freq_min"),
                               MTS_AUDIBLE_WAVELENGTH_MAX);

        if (props.has_property("freq_max"))
            m_lambda_min = min(MTS_SOUND_SPEED / props.float_("freq_max"),
                               MTS_AUDIBLE_WAVELENGTH_MIN);

        if (!(m_lambda_min < m_lambda_max))
            Throw(
                "AudibleSpectrum: 'lambda_min' must be less than 'lambda_max'");

        // **************** Copied from irregular ****************************

        // Are the supplied values for absorption or reflectance?
        bool absorption = props.bool_("absorption", true);

        if (props.has_property("value")) {
            m_values.reserve(1);
            ScalarFloat v = props.float_("value");
            v = absorption ? 1 - v : v;
            m_values.push_back(v);
            return;
        }

        bool has_wavs = props.has_property("wavelengths");
        auto str      = has_wavs ? "wavelengths" : "frequencies";

        if (props.has_property(str)) {

            std::vector<std::string> wavelengths_str =
                string::tokenize(props.string(str), " ,");

            std::vector<std::string> entry_str,
                values_str = string::tokenize(props.string("values"), " ,");

            if (values_str.size() != wavelengths_str.size())
                Throw("IrregularSpectrum: 'wavelengths'/'frequencies' and "
                      "'values' "
                      "parameters "
                      "must have the same size!");

            m_values.reserve(values_str.size());
            m_wavelengths.reserve(values_str.size());

            for (size_t i = 0; i < values_str.size(); ++i) {
                try {
                    ScalarFloat wav = std::stod(wavelengths_str[i]);
                    // Is this value actually a frequency?
                    wav = has_wavs ? wav : MTS_SOUND_SPEED / wav;
                    m_wavelengths.push_back(wav);
                } catch (...) {
                    Throw("Could not parse floating point value '%s'",
                          wavelengths_str[i]);
                }
                try {
                    auto v = (ScalarFloat) std::stod(values_str[i]);
                    v = absorption ? 1 - v : v;
                    m_values.push_back(v);
                } catch (...) {
                    Throw("Could not parse floating point value '%s'",
                          values_str[i]);
                }
            }

            // Frequencies were converted to wavelengths. We need to reverse the order
            if (!has_wavs) {
                std::reverse(m_wavelengths.begin(), m_wavelengths.end());
                std::reverse(m_values.begin(), m_values.end());
            }
        } else {
            // Initialize with fractional octaves
            int b = props.int_("octave_step_width");
            m_wavelengths =
                fractional_octaves(b, { m_lambda_min, m_lambda_max }, all);

            // Copy wavelengths to values
            m_values = m_wavelengths;

            // Invert
            std::transform(m_values.begin(), m_values.end(), m_values.begin(),
                           [](auto &&x) {
                               return std::divides()(
                                   MTS_SOUND_SPEED,
                                   std::forward<decltype(x)>(x));
                           });

            // Normalize
            ScalarFloat norm =
                std::accumulate(m_values.begin(), m_values.end(), 0.f);
            std::transform(m_values.begin(), m_values.end(), m_values.begin(),
                           [norm](auto &&x) {
                               return std::divides()(
                                   std::forward<decltype(x)>(x),
                                   norm);
                           });
        }
        // ********************************************************************
    }

    std::vector<ref<Object>> expand() const override {
        Properties props;
        // If we only have one value we want the spectrum to be uniform
        if(m_values.size() == 1) {
            props = Properties("uniform");
            props.set_float("value", m_values.at(0));
        } else {
            // This plugin recursively expands into an instance of 'irregular'
            props = Properties("irregular");
            props.set_int("size", m_values.size());

            props.set_pointer("values", (const void *) &m_values[0]);
            props.set_pointer("wavelengths", (const void *) &m_wavelengths[0]);
        }
        PluginManager *pmgr = PluginManager::instance();
        return { ref<Object>(pmgr->create_object<Texture>(props)) };
    }

    UnpolarizedSpectrum eval(const SurfaceInteraction3f &si,
                             Mask active) const override {
        MTS_MASKED_FUNCTION(ProfilerPhase::TextureEvaluate, active);

        if constexpr (is_spectral_v<Spectrum>) {
            auto active_w = (si.wavelengths >= m_lambda_min) &&
                            (si.wavelengths <= m_lambda_max);

            NotImplementedError("eval");
        } else {
            Throw("AudibleSpectrum: only works with spectral rendering");
        }
    }

//    Wavelength pdf_spectrum(const SurfaceInteraction3f &si,
//                            Mask active) const override {
//        MTS_MASKED_FUNCTION(ProfilerPhase::TextureEvaluate, active);
//
//        if constexpr (is_spectral_v<Spectrum>) {
//            auto active_w = (si.wavelengths >= m_lambda_min) &&
//                            (si.wavelengths <= m_lambda_max);
//
//            NotImplementedError("pdf_spectrum");
//        } else {
//            Throw("AudibleSpectrum: only works with spectral rendering");
//        }
//    }

//    std::pair<Wavelength, UnpolarizedSpectrum>
//    sample_spectrum(const SurfaceInteraction3f & /*si*/,
//                    const Wavelength &sample, Mask active) const override {
//        MTS_MASKED_FUNCTION(ProfilerPhase::TextureSample, active);
//
//        if constexpr (is_spectral_v<Spectrum>) {
//            NotImplementedError("sample_spectrum");
//        } else {
//            ENOKI_MARK_USED(sample);
//            Throw("AudibleSpectrum: only works with spectral rendering");
//        }
//    }

    ScalarFloat mean() const override { return 1.0; }

    void traverse(TraversalCallback *callback) override {
        callback->put_parameter("lambda_min", m_lambda_min);
        callback->put_parameter("lambda_max", m_lambda_max);
    }

    std::string to_string() const override {
        std::ostringstream oss;
        oss << "AudibleSpectrum[" << std::endl
            << "  lambda_min = " << m_lambda_min << std::endl
            << "  lambda_max = " << m_lambda_max << std::endl
            << "]";
        return oss.str();
    }

    MTS_DECLARE_CLASS()
private:
    /**
     * Calculate fractional octave frequencies according to [1]_.
     * \param b
     *      Defines the setpwith, e.g., 3=third octaves and 1=octaves.
     * \param range
     *      Minimum and maximum center frequency in Hz to be calculated.
     * \param band_type
     *      Low, Center, High or all frequencies together?
     *      Default: center
     * \param f_ref
     *      Reference frequency
     *
     * .. [1] IEC 61260-1, Octave-band and fractional-octave-band filters.
     *    Part 1: Specifications, 2014.
     *
     * \return
     */
    std::vector<ScalarFloat> fractional_octaves(const ssize_t b,
                                                const ScalarPoint2f &range,
                                                const bands band_type = center,
                                                const float f_ref     = 1000) {

        const float B = powf(10, 3.f / 10.f);
        std::vector<ScalarFloat> result;
        int i        = 0;
        bool forward = true;
        float frac   = band_type == all ? b * 2.f : b;
        float eps    = band_type == all || band_type == high ? 0.002f : 0.f;

        while (true) {
            float val;

            // Compute wavelength
            if (b % 2) {
                val = MTS_SOUND_SPEED / (powf(B, float(i) / frac) * f_ref);
            } else {
                val = MTS_SOUND_SPEED /
                      (powf(B, (2 * float(i) + 1) / 2 * frac) * f_ref);
            }

            switch (band_type) {
                case low:
                    val *= powf(B, -1.f / (2.f * frac));
                    break;
                case high:
                    val *= powf(B, 1.f / (2.f * frac));
                    break;
                default:
                    break;
            }

            // Upper bound reached go backward
            if (val + eps < range[0]) {
                i       = -1;
                forward = false;
                continue;
            }
            // Lower bound reached. Quit
            if (val > range[1])
                break;

            // Store value
            result.push_back(val);

            // Are we going forward or backwards?
            forward ? i++ : i--;
        }
        std::sort(result.begin(), result.end(), std::less<>());
        return result;
    }

    ScalarFloat m_lambda_min;
    ScalarFloat m_lambda_max;
    std::vector<ScalarFloat> m_values, m_wavelengths;
};

MTS_IMPLEMENT_CLASS_VARIANT(AcousticSpectrum, Texture)
MTS_EXPORT_PLUGIN(AcousticSpectrum, "Audible spectrum")
NAMESPACE_END(mitsuba)
