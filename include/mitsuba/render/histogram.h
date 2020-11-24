#pragma once

#include <mitsuba/core/fwd.h>
#include <mitsuba/core/object.h>
#include <mitsuba/core/vector.h>
#include <mitsuba/render/fwd.h>

NAMESPACE_BEGIN(mitsuba)

template <typename Float, typename Spectrum>
class MTS_EXPORT_RENDER Histogram : public Object {
public:
    /**
     * Construct a new histogram
     *
     * \param bin_count
     *    discretize wavelengths into this many bins
     * \param time_step_count
     *    defines the amount of time
     * \param range
     *    the wavelength range to be recorded
     *
     */
    Histogram(size_t bin_count, size_t time_step_count, ScalarPoint2f range);

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
     * \return
     */
    Mask put(const UInt32 &time_step, const Wavelength &wavelengths, const Spectrum &value, Mask active = true);

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
    ScalarPoint2f range() { return m_range; }

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
     * discretization of the different wavelength bins
     *
     * \param value
     *    The value of a wavelength
     *
     */
    UInt32 bin_index(const Float value) {
        const float bin_size = m_range.y() - m_range.x();
        const float discretizer = bin_size / m_bin_count;
        // Integer division
        return (value - m_range.x()) / discretizer;
    }

protected:
    size_t m_bin_count;
    size_t m_time_step_count;
    ScalarPoint2f m_range;
    DynamicBuffer<Float> m_data;
};

MTS_EXTERN_CLASS_RENDER(Histogram)
NAMESPACE_END(mitsuba)
