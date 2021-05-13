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
    MTS_IMPORT_TYPES()

    Histogram(const ScalarVector2u &size, size_t channel_count);

    /**
     * Construct a new histogram with the specified amount of bins for wavelengths / time
     * @param n_time_bins
     * @param n_wavelength_bins
     */
    Histogram(const ScalarUInt32 n_time_bins, const ScalarUInt32 n_wavelength_bins);

    /**
     * \brief Insert Wavelength samples at discrete position
     *
     * \param pos
     *     wavelength bin and time bin
     * \param value
     *     Intensity value for this wavelength and time
     * \param active
     *     Mask indicating enabled state
     * \returns
     *     False if the sample was invalid. E.g not in range or NaN
     */
    Mask put(const Point2f &pos, const Spectrum &value, Mask active = true);

    Mask put(const Point2f &pos, const Float *value, Mask active = true);

    /**
     * For now we simply overwrite the storage
     * In the future it could be beneficial to be able to merge histograms
     */
    void put(const Histogram * hist);

    /// Clear everything to zero.
    void clear();

    // =============================================================
    //! @{ \name Accesors
    // =============================================================

    /// Set the current hist offset.
    void set_offset(const ScalarPoint2i &offset) { m_offset = offset; }

    /// Return the current histogram size
    const ScalarVector2i &size() const { return m_size; }

    /// Return the width (time bins)
    size_t width() const { return m_size.x(); }

    /// Return the height (wav bins)
    size_t height() const { return m_size.y(); }

    /// Return the current hist offset
    const ScalarPoint2i &offset() const { return m_offset; }

    /// Return the underlying spectrum buffer
    DynamicBuffer<Float> &data() { return m_data; }

    /// Return the underlying spectrum buffer (const version)
    const DynamicBuffer<Float> &data() const { return m_data; }

    /// Return the underlying counts for every bin
    DynamicBuffer<UInt32> &counts() { return m_counts; }

    /// Return the underlying counts for every bin (const version)
    const DynamicBuffer<UInt32> &counts() const { return m_counts; }

    //! @}
    // =============================================================

    std::string to_string() const override;

    MTS_DECLARE_CLASS()

protected:
    /// Virtual destructor
    virtual ~Histogram();

protected:
    size_t m_channel_count;
    ScalarVector2i m_size;
    ScalarPoint2i m_offset;
    DynamicBuffer<Float> m_data;
    DynamicBuffer<UInt32> m_counts;
};

MTS_EXTERN_CLASS_RENDER(Histogram)
NAMESPACE_END(mitsuba)
