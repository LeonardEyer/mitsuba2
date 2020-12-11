#pragma once

#include <mitsuba/core/fwd.h>
#include <mitsuba/core/object.h>
#include <mitsuba/core/vector.h>
#include <mitsuba/render/fwd.h>

NAMESPACE_BEGIN(mitsuba)

/**
 * \brief Storage for the energy decay envelope of all recorded spectral
 * wavelengths
 *
 * This class contains all the information regarding the decay of energy per
 * wavelength. For each (discrete) time step the recorded energy can be stored.
 */
template <typename Float, typename Spectrum>
class MTS_EXPORT_RENDER Histogram : public Object {
public:
    /**
     * Construct a new histogram for the logging of wavelengths over time
     *
     * \param bin_count
     *    discretize wavelengths into this many bins
     * \param time_step_count
     *    discretize time into this many bins
     * \param wav_range
     *    the wavelength range to be recorded
     * \param time_range
     *    the time range to be recorded
     *
     */
    Histogram(size_t bin_count, size_t time_step_count,
              const ScalarPoint2f &wav_range, const ScalarPoint2f &time_range);

    /**
     * Construct a new histogram for the logging of wavelengths over time
     * using predefined wavelength bins
     *
     * \param time_step_count
     *    discretize time into this many bins
     * \param time_range
     *    the time range to be recorded
     * \param wavelength_bins
     *    array of bins we want to log the wavelengths in
     *
     */
    Histogram(size_t time_step_count,
              const ScalarPoint2f &time_range,
              const std::vector<float> &wavelength_bins);

    /**
     * \brief Insert Wavelength samples with corresponding time indices
     *
     * \param time_step
     *     Recorded time of this sample
     * \param wavelengths
     *     The sampled wavelength
     * \param value
     *     Intensity value for this wavelength
     * \param active
     *     Mask indicating enabled state
     * \returns
     *     False if the sample was invalid. E.g not in range or NaN
     */
    Mask put(const Float &time_step, const Wavelength &wavelength,
             const Spectrum &value, Mask active = true);

    /// Clear everything to zero.
    void clear();

    // =============================================================
    //! @{ \name Accesors
    // =============================================================

    /// Return the number of stored bins
    size_t bin_count() { return m_bin_count; }

    /// Return the count of recordable time steps
    size_t time_step_count() { return m_time_step_count; }

    // Return the wavelength range this histogram is recording
    ScalarPoint2f wav_range() { return m_wav_range; }

    // Return the time range this histogram is recording
    ScalarPoint2f time_range() { return m_time_range; }

    // Return the predefined wavelength bins
    std::vector<float> wavelength_bins() { return m_wavelength_bins; }

    /// Return the underlying spectrum buffer
    DynamicBuffer<Float> &data() { return m_data; }

    /// Return the underlying spectrum buffer (const version)
    const DynamicBuffer<Float> &data() const { return m_data; }

    //! @}
    // =============================================================

    std::string to_string() const override;

    MTS_DECLARE_CLASS()
protected:
    /// Virtual destructor
    virtual ~Histogram();

    /**
     * Compute the bin index of this value. This is needed for the
     * discretization of the different wavelength and time bins
     *
     * \param value
     *    The value to be discretizied
     *
     */
    UInt32 discretize(const Float value, const ScalarPoint2f range,
                      ssize_t n_steps) {
        const float bin_size    = range.y() - range.x();
        const float discretizer = bin_size / n_steps;
        // Integer division
        return (value - range.x()) / discretizer;
    }

    /**
     * Compute the bin index of this value given an array of preset bins
     * \param value
     *      The value to be discretized
     * \param preset_bins
     *      The array of bins
     * \returns
     *      The computed index
     * greater or equal to max bin)
     */
    UInt32 discretize_preset_bins(const Float value,
                                const std::vector<float> &preset_bins) {

        UInt32 index = -1;
        for (size_t i = 1; i < preset_bins.size(); ++i) {
            // bins[i-1] <= value < bins[i]
            Mask mask =
                preset_bins.at(i - 1) <= value && value < preset_bins.at(i);

            masked(index, mask) = (i - 1);
        }
        return index;
    }

protected:
    size_t m_bin_count;
    size_t m_time_step_count;
    ScalarPoint2f m_wav_range;
    ScalarPoint2f m_time_range;
    std::vector<float> m_wavelength_bins;
    DynamicBuffer<Float> m_data;
};

MTS_EXTERN_CLASS_RENDER(Histogram)
NAMESPACE_END(mitsuba)
