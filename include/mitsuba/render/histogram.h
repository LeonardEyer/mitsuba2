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
    Histogram(size_t bin_count, size_t time_step_count, ScalarPoint2f wav_range,
              ScalarPoint2f time_range);

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
    UInt32 discretize(const Float value, ScalarPoint2f range, ssize_t n_steps) {
        const float bin_size    = range.y() - range.x();
        const float discretizer = bin_size / n_steps;
        // Integer division
        return (value - range.x()) / discretizer;
    }

protected:
    size_t m_bin_count;
    size_t m_time_step_count;
    ScalarPoint2f m_wav_range;
    ScalarPoint2f m_time_range;
    DynamicBuffer<Float> m_data;
};

MTS_EXTERN_CLASS_RENDER(Histogram)
NAMESPACE_END(mitsuba)
