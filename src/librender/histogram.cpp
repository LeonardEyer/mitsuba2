#include <mitsuba/render/histogram.h>


NAMESPACE_BEGIN(mitsuba)

MTS_VARIANT Histogram<Float, Spectrum>::Histogram() {}

    // Allocate empty buffer
    m_data = empty<DynamicBuffer<Float>>(time_step_count * channel_count);
}

MTS_VARIANT typename Histogram<Float, Spectrum>::Mask
Histogram<Float, Spectrum>::put(const UInt32 &time_step, const Spectrum &value,
                                Mask active) {

    size_t max = m_time_step_count;
    UInt32 offset = (time_step * m_channel_count);
    Mask enabled = active && all(time_step >= 0u && time_step < max);

    for (int i = 0; i < m_channel_count; ++i) {
        scatter_add(m_data, value[i], offset + i, enabled);
    }

    return enabled;
}

MTS_VARIANT void Histogram<Float, Spectrum>::clear() {
    size_t size = m_time_step_count * m_channel_count;
    if constexpr (!is_cuda_array_v<Float>)
        memset(m_data.data(), 0, size * sizeof(ScalarFloat));
    else
        m_data = zero<DynamicBuffer<Float>>(size);
}

MTS_VARIANT Histogram<Float, Spectrum>::~Histogram() {}

MTS_VARIANT std::string Histogram<Float, Spectrum>::to_string() const {
    std::ostringstream oss;
    oss << "Histogram[" << std::endl
        << "]";
    return oss.str();
}

MTS_IMPLEMENT_CLASS_VARIANT(Histogram, Object)
MTS_INSTANTIATE_CLASS(Histogram)
NAMESPACE_END(mitsuba)
