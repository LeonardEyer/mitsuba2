#pragma once

#include <mitsuba/core/fwd.h>
#include <mitsuba/core/object.h>
#include <mitsuba/core/vector.h>
#include <mitsuba/render/fwd.h>

NAMESPACE_BEGIN(mitsuba)

/**
 * \brief Storage for the energy decay envelope of all recorded spectral
 * frequencies
 *
 * This class contains all the information regarding the decay of energy per
 * frequency. For each (discrete) time step the recorded energy can be stored.
 */
template <typename Float, typename Spectrum>
class MTS_EXPORT_RENDER Histogram : public Object {
    MTS_IMPORT_TYPES()
public:
    /**
     * Construct a new histogram
     *
     * \param channel_count
     *    how many frequencies should be recorded
     * \param time_step_count
     *    defines the amount of time slots
     */
    Histogram(int channel_count, int time_step_count);

    /**
     * Insert spectral values with corresponding time indices
     */
    Mask put(const UInt32 &time_step, const Spectrum &value, Mask active = true);

    /// Clear everything to zero.
    void clear();

    // =============================================================
    //! @{ \name Accesors
    // =============================================================

    /// Return the number of channels stored
    int channel_count() { return m_channel_count; }

    /// Return the count of recordable time steps
    int time_step_count() { return m_time_step_count; }

    //! @}
    // =============================================================

    std::string to_string() const override;

    MTS_DECLARE_CLASS()
protected:
    /// Virtual destructor
    virtual ~Histogram();

protected:
    int m_channel_count;
    int m_time_step_count;
    DynamicBuffer<Spectrum> m_data;
};

MTS_EXTERN_CLASS_RENDER(Histogram)
NAMESPACE_END(mitsuba)
