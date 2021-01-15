#include <mitsuba/render/histogram.h>
#include <mitsuba/core/profiler.h>

NAMESPACE_BEGIN(mitsuba)

MTS_VARIANT
Histogram<Float, Spectrum>::Histogram(size_t bin_count, size_t time_step_count,
                                      const ScalarPoint2f &wav_range,
                                      const ScalarPoint2f &time_range)
    : m_bin_count(bin_count), m_time_step_count(time_step_count),
      m_wav_range(wav_range), m_time_range(time_range) {

    if (wav_range.y() < wav_range.x() or time_range.y() < time_range.x()) {
        Throw("Histogram: lower bound of range must be smaller than upper");
    }
    if (any(wav_range < 0.f) or any(time_range < 0.f)) {
        Throw("Histogram: only positive wavelength/time range allowed");
    }

    // Allocate empty buffer
    m_data = empty<DynamicBuffer<Float>>(time_step_count * bin_count);
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
    UInt32 offset = (discrete_time_step * m_bin_count);

    Mask enabled =
        active &&
        all(time_step >= m_time_range[0] && time_step < m_time_range[1]) &&
        all(wavelengths >= m_wav_range[0] && wavelengths < m_wav_range[1]);

    for (size_t i = 0; i < value.size(); ++i) {
        Float lambda = wavelengths[i];
        Float val    = value[i];
        UInt32 bidx;

        bidx = discretize_preset_bins(lambda, m_wavelength_bins);

        scatter_add(m_data, val, offset + bidx, enabled);
    }

    return enabled;
}

MTS_VARIANT void Histogram<Float, Spectrum>::put(const Histogram *hist) {
    ScopedPhase sp(ProfilerPhase::HistogramPut);

    /*if (likely(hist->bin_count() != bin_count())) {
        return;
    }*/
    m_data = hist->data();

}


MTS_VARIANT void Histogram<Float, Spectrum>::clear() {
    size_t size = m_time_step_count * m_bin_count;
    if constexpr (!is_cuda_array_v<Float>)
        memset(m_data.data(), 0, size * sizeof(ScalarFloat));
    else
        m_data = zero<DynamicBuffer<Float>>(size);
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
