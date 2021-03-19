#include <mitsuba/core/bitmap.h>
#include <mitsuba/core/profiler.h>
#include <mitsuba/render/histogram.h>

NAMESPACE_BEGIN(mitsuba)

MTS_VARIANT
Histogram<Float, Spectrum>::Histogram(size_t bin_count, size_t time_step_count,
                                      const ScalarPoint2f &wav_range,
                                      const ScalarPoint2f &time_range)
    : m_bin_count(bin_count), m_time_step_count(time_step_count),
      m_channel_count(1), m_size({ bin_count, time_step_count }),
      m_wav_range(wav_range), m_time_range(time_range), m_offset(0) {

    if (wav_range.y() < wav_range.x() or time_range.y() < time_range.x()) {
        Throw("Histogram: lower bound of range must be smaller than upper");
    }
    if (any(wav_range < 0.f) or any(time_range < 0.f)) {
        Throw("Histogram: only positive wavelength/time range allowed");
    }

    // Allocate empty buffer
    m_data = empty<DynamicBuffer<Float>>(hprod(m_size));
    m_counts = empty<DynamicBuffer<UInt32>>(hprod(m_size));
}

MTS_VARIANT
Histogram<Float, Spectrum>::Histogram(size_t time_step_count,
                                      const ScalarPoint2f &time_range,
                                      const std::vector<float> &wavelength_bins)
    : Histogram(wavelength_bins.size() - 1, time_step_count,
                { wavelength_bins.front(), wavelength_bins.back() },
                time_range) {

    m_wavelength_bins = wavelength_bins;
}

MTS_VARIANT typename Histogram<Float, Spectrum>::Mask
Histogram<Float, Spectrum>::put(const Float &time_step,
                                const Wavelength &wavelengths,
                                const Spectrum &value, Mask active) {
    ScopedPhase sp(ProfilerPhase::HistogramPut);

    UInt32 discrete_time_step =
        discretize_linear(time_step, m_time_range, m_time_step_count);

    Mask enabled =
        active && all(value >= 0) &&
        all(time_step >= m_time_range[0] && time_step < m_time_range[1]) &&
        all(wavelengths >= m_wav_range[0] && wavelengths < m_wav_range[1]);

    for (size_t i = 0; i < value.size(); ++i) {
        Float lambda = wavelengths[i];
        Float val    = value[i];
        UInt32 bidx;

        bidx = discretize_preset_bins(lambda, m_wavelength_bins);
        Point2u pos = { bidx - 1, discrete_time_step };
        put(pos, &val, enabled);
    }

    return enabled;
}

MTS_VARIANT typename Histogram<Float, Spectrum>::Mask
Histogram<Float, Spectrum>::put(const Point2u &pos, const Float *value,
                                Mask active) {
    Mask enabled = active && all(pos >= 0u && pos < m_size);

    UInt32 offset = m_channel_count * (pos.y() * m_size.x() + pos.x());

    ENOKI_NOUNROLL for (uint32_t k = 0; k < m_channel_count; ++k) {
        scatter_add(m_data, value[k], offset + k, enabled);
        scatter_add(m_counts, UInt32(1), offset + k, enabled);
    }

    return enabled;
};

MTS_VARIANT void Histogram<Float, Spectrum>::put(const Histogram *hist) {
    ScopedPhase sp(ProfilerPhase::HistogramPut);

    size_t time_steps = time_step_count();
    size_t n_bins     = bin_count();

    ScalarVector2i source_size = { hist->bin_count(), hist->time_step_count() },
                   target_size = { n_bins, time_steps };

    ScalarPoint2i source_offset = hist->offset(), target_offset = offset();

    if constexpr (is_cuda_array_v<Float> || is_diff_array_v<Float>) {
        accumulate_2d<Float &, const Float &>(
            hist->data(), source_size, data(), target_size, ScalarVector2i(0),
            source_offset - target_offset, source_size, 1);

        accumulate_2d<UInt32 &, const UInt32 &>(
            hist->counts(), source_size, counts(), target_size, ScalarVector2i(0),
            source_offset - target_offset, source_size, 1);

    } else {
        accumulate_2d(hist->data().data(), source_size, data().data(),
                      target_size, ScalarVector2i(0),
                      source_offset - target_offset, source_size, 1);

        accumulate_2d(hist->counts().data(), source_size, counts().data(),
                      target_size, ScalarVector2i(0),
                      source_offset - target_offset, source_size, 1);
    }
}

MTS_VARIANT void Histogram<Float, Spectrum>::clear() {
    size_t size = m_time_step_count * m_bin_count;
    if constexpr (!is_cuda_array_v<Float>) {
        memset(m_data.data(), 0, size * sizeof(ScalarFloat));
        memset(m_counts.data(), 0, size * sizeof(ScalarUInt32));
    } else {
            m_data   = zero<DynamicBuffer<Float>>(size);
            m_counts = zero<DynamicBuffer<UInt32>>(size);
    }
}

MTS_VARIANT Histogram<Float, Spectrum>::~Histogram() {}

MTS_VARIANT std::string Histogram<Float, Spectrum>::to_string() const {
    std::ostringstream oss;
    oss << "Histogram[" << std::endl
        << "  bin_count = " << m_bin_count << "," << std::endl
        << "  time_step_count = " << m_time_step_count << "," << std::endl
        << "  wav_range = " << m_wav_range << "," << std::endl
        << "  time_range = " << m_time_range << "," << std::endl
        << "]";
    return oss.str();
}

MTS_IMPLEMENT_CLASS_VARIANT(Histogram, Object)
MTS_INSTANTIATE_CLASS(Histogram)
NAMESPACE_END(mitsuba)
