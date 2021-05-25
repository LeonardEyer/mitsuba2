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
    MTS_IMPORT_TYPES(ReconstructionFilter)

     /**
      * \brief Construct a new histogram with the specified amount of bins for wavelengths / time
      *
      * \param size
      *     number of time bins, number of wavelength bins
      * \param channel_count
      *     channel count is currently expected to always be 1
      * \param filter
      *     reconstruction filter to be applied along the time axis
      * \param border
      *     enable usage of border region for wide reconstruction filter (non box)
      */
    Histogram(const ScalarVector2i &size,
              size_t channel_count,
              const ReconstructionFilter *filter = nullptr,
              bool border = true);

    /**
     * \brief Insert Wavelength samples at discrete position
     *
     * \param pos
     *     time bin and wavelength bin
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
     * Merge two histograms (simply adding all the recorded data and weights)
     */
    void put(const Histogram * hist);

    /// Clear everything to zero.
    void clear();

    // =============================================================
    //! @{ \name Accesors
    // =============================================================

    /// Set the current hist offset.
    void set_offset(const ScalarPoint2i &offset) { m_offset = offset; }

    /// Set the block size. This potentially destroys the hist's content.
    void set_size(const ScalarVector2i &size);

    /// Return the current histogram size
    const ScalarVector2i &size() const { return m_size; }

    /// Return the width (time bins)
    size_t width() const { return m_size.x(); }

    /// Return the height (wav bins)
    size_t height() const { return m_size.y(); }

    /// Return the number of channels stored by the histogram
    size_t channel_count() const { return (size_t) m_channel_count; }

    /// Return the border region used by the reconstruction filter
    int border_size() const { return m_border_size; }

    /// Return the current hist offset
    const ScalarPoint2i &offset() const { return m_offset; }

    /// Return the underlying spectrum buffer
    DynamicBuffer<Float> &data() { return m_data; }

    /// Return the underlying spectrum buffer (const version)
    const DynamicBuffer<Float> &data() const { return m_data; }

    /// Return the underlying counts for every bin
    DynamicBuffer<Float> &counts() { return m_counts; }

    /// Return the underlying counts for every bin (const version)
    const DynamicBuffer<Float> &counts() const { return m_counts; }

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
    int m_border_size;
    DynamicBuffer<Float> m_data;
    DynamicBuffer<Float> m_counts;
    const ReconstructionFilter *m_filter;
    Float *m_weights;
};

MTS_EXTERN_CLASS_RENDER(Histogram)
NAMESPACE_END(mitsuba)
