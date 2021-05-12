#include <mitsuba/core/bitmap.h>
#include <mitsuba/core/profiler.h>
#include <mitsuba/render/histogram.h>

NAMESPACE_BEGIN(mitsuba)

MTS_VARIANT
Histogram<Float, Spectrum>::Histogram(const ScalarVector2u &size, size_t channel_count)
    : m_channel_count(channel_count), m_size(size), m_offset(0) {

    // Allocate empty buffer
    m_data = empty<DynamicBuffer<Float>>(hprod(m_size));
    m_counts = empty<DynamicBuffer<UInt32>>(hprod(m_size));
}

MTS_VARIANT
Histogram<Float, Spectrum>::Histogram(const ScalarUInt32 n_time_bins, const ScalarUInt32 n_wavelength_bins) :
    Histogram({n_time_bins, n_wavelength_bins}, 1) { }

MTS_VARIANT typename Histogram<Float, Spectrum>::Mask
Histogram<Float, Spectrum>::put(const Point2f &pos,
                                const Spectrum &value,
                                Mask active) {

    for (size_t i = 0; i < value.size(); ++i) {
        Float val = value[i];
        active &= put(pos, &val, active);
    }

    return active;
}

MTS_VARIANT typename Histogram<Float, Spectrum>::Mask
Histogram<Float, Spectrum>::put(const Point2f &pos_, const Float *value,
                                Mask active) {
    Point2f pos = pos_ - m_offset;
    Mask enabled = active && all(pos >= 0u && pos < m_size);

    UInt32 offset = m_channel_count * (pos.x() * m_size.y() + pos.y());

    ENOKI_NOUNROLL for (uint32_t k = 0; k < m_channel_count; ++k) {
        scatter_add(m_data, value[k], offset + k, enabled);
        scatter_add(m_counts, UInt32(1), offset + k, enabled);
    }

    return enabled;
};

MTS_VARIANT void Histogram<Float, Spectrum>::put(const Histogram *hist) {
    ScopedPhase sp(ProfilerPhase::HistogramPut);

    ScalarVector2i source_size = {hist->size().y(),  hist->size().x()},
    target_size = {size().y(),  size().x()};

    ScalarPoint2i source_offset = {hist->offset().y(), hist->offset().x()},
        target_offset = {offset().y(), offset().x()};

/*    ScalarVector2i source_size = hist->size(), target_size = size();
    ScalarPoint2i source_offset = hist->offset(), target_offset = offset();*/

    if constexpr (is_cuda_array_v<Float> || is_diff_array_v<Float>) {
        accumulate_2d<Float &, const Float &>(
            hist->data(), source_size, data(), target_size, ScalarVector2i(0),
            source_offset - target_offset, source_size, m_channel_count);

        accumulate_2d<UInt32 &, const UInt32 &>(
            hist->counts(), source_size, counts(), target_size, ScalarVector2i(0),
            source_offset - target_offset, source_size, m_channel_count);

    } else {
        accumulate_2d(hist->data().data(), source_size, data().data(),
                      target_size, ScalarVector2i(0),
                      source_offset - target_offset, source_size, m_channel_count);

        accumulate_2d(hist->counts().data(), source_size, counts().data(),
                      target_size, ScalarVector2i(0),
                      source_offset - target_offset, source_size, m_channel_count);
    }
}

MTS_VARIANT void Histogram<Float, Spectrum>::clear() {
    if constexpr (!is_cuda_array_v<Float>) {
        memset(m_data.data(), 0, hprod(m_size) * sizeof(ScalarFloat));
        memset(m_counts.data(), 0, hprod(m_size) * sizeof(ScalarUInt32));
    } else {
        m_data = zero<DynamicBuffer<Float>>(hprod(m_size));
        m_counts = zero<DynamicBuffer<UInt32>>(hprod(m_size));
    }
}

MTS_VARIANT Histogram<Float, Spectrum>::~Histogram() {}

MTS_VARIANT std::string Histogram<Float, Spectrum>::to_string() const {
    std::ostringstream oss;
    oss << "Histogram[" << std::endl
        << "  bin_count = " << height() << "," << std::endl
        << "  time_step_count = " << width() << "," << std::endl
        << "]";
    return oss.str();
}

MTS_IMPLEMENT_CLASS_VARIANT(Histogram, Object)
MTS_INSTANTIATE_CLASS(Histogram)
NAMESPACE_END(mitsuba)
