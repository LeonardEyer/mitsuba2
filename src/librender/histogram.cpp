#include <mitsuba/render/histogram.h>

NAMESPACE_BEGIN(mitsuba)

MTS_VARIANT Histogram<Float, Spectrum>::Histogram(int channel_count,
                                                  int time_step_count)
    : m_channel_count(channel_count), m_time_step_count(time_step_count) {

    // Allocate empty buffer
    m_data = empty<DynamicBuffer<Spectrum>>(time_step_count);
}

MTS_VARIANT typename Histogram<Float, Spectrum>::Mask
Histogram<Float, Spectrum>::put(const UInt32 &time_step, const Spectrum &value,
                                Mask active) {
    return active;
}

MTS_VARIANT void Histogram<Float, Spectrum>::clear() {
    size_t size = m_time_step_count;
    if constexpr (!is_cuda_array_v<Float>)
        Throw("\"clear\" not implemented for gpu variant");
        //memset(m_data.data(), 0, size * m_channel_count* sizeof(ScalarFloat));
    else
        m_data = zero<DynamicBuffer<Spectrum>>(size);
}

MTS_VARIANT Histogram<Float, Spectrum>::~Histogram() {}

MTS_VARIANT std::string Histogram<Float, Spectrum>::to_string() const {
    std::ostringstream oss;
    oss << "Histogram[" << std::endl
        << "  channel_count = " << m_channel_count << "," << std::endl
        << "  time_step_count = " << m_time_step_count << "," << std::endl
        << "]";
    return oss.str();
}

MTS_IMPLEMENT_CLASS_VARIANT(Histogram, Object)
MTS_INSTANTIATE_CLASS(Histogram)
NAMESPACE_END(mitsuba)
