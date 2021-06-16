#include <mitsuba/core/bitmap.h>
#include <mitsuba/core/profiler.h>
#include <mitsuba/render/histogram.h>
#include <algorithm>

NAMESPACE_BEGIN(mitsuba)

MTS_VARIANT
Histogram<Float, Spectrum>::Histogram(const ScalarVector2i &size,
                                      size_t channel_count,
                                      const ReconstructionFilter *filter,
                                      bool border)
    : m_channel_count((uint32_t) channel_count), m_size(0), m_offset(0), m_filter(filter), m_weights(nullptr) {

    m_border_size = (uint32_t) ((filter != nullptr && border) ? filter->border_size() : 0);

    if (filter) {
        // Temporary buffers used in put()
        int filter_size = (int) std::ceil(2 * filter->radius()) + 1;
        m_weights = new Float[filter_size];
    }

    set_size(size);
}

MTS_VARIANT Histogram<Float, Spectrum>::~Histogram() {
    if (m_weights)
        delete[] m_weights;
}


MTS_VARIANT void Histogram<Float, Spectrum>::clear() {

    size_t size = m_channel_count * hprod(m_size + 2 * ScalarVector2i(m_border_size, 0));

    if constexpr (!is_cuda_array_v<Float>) {
        memset(m_data.data(), 0, size * sizeof(ScalarFloat));
        memset(m_counts.data(), 0, size * sizeof(ScalarUInt32));

        // if (m_border_size == 0) return;

        // for (int i = 0; i < m_border_size; ++i) {
        //     m_data.data()[i] = 1;
        //     m_counts.data()[i] = 1;
        // }
    } else {
        m_data = zero<DynamicBuffer<Float>>(size);
        m_counts = zero<DynamicBuffer<UInt32>>(size);

        // if (m_border_size == 0) return;

        // UInt32 idx = arange<UInt32>(m_border_size);
        // scatter_add(m_data, Float(1.), idx);
        // scatter_add(m_counts, Float(1.), idx);
    }
}

MTS_VARIANT void Histogram<Float, Spectrum>::normalize() {

    size_t size = m_channel_count * hprod(m_size + 2 * ScalarVector2i(m_border_size, 0));
    auto idx = arange<UInt32>(size);

    auto d = gather<Float>(m_data, idx) / gather<UInt32>(m_counts, idx);

    scatter(m_data, d, idx);
    scatter(m_counts, UInt32(1), idx);

}

MTS_VARIANT void Histogram<Float, Spectrum>::set_size(const ScalarVector2i &size) {
    if (size == m_size)
        return;
    m_size = size;

    size_t total_size = m_channel_count * hprod(size + 2 * ScalarVector2i(m_border_size, 0));

    // Allocate empty buffer
    m_data = empty<DynamicBuffer<Float>>(hprod(total_size));
    m_counts = empty<DynamicBuffer<UInt32>>(hprod(total_size));
}

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
    ScopedPhase sp(ProfilerPhase::HistogramPut);
    assert(m_filter != nullptr);

    Point2f pos = pos_ - (m_offset + Point2f(- m_border_size + .5f, 0.f));
    ScalarVector2i size = m_size + ScalarVector2i(2 * m_border_size, 0);

    if (m_filter->radius() > 0.5f + math::RayEpsilon<Float>) {
        // Determine the affected range of time bins
        Point2u lo = Point2u(max(ceil2int <Point2i>(pos - Point2f(m_filter->radius(), 0)), 0)),
                hi = Point2u(min(floor2int<Point2i>(pos + Point2f(m_filter->radius(), 0)), size - ScalarVector2i(1, 0)));

        uint32_t n = ceil2int<uint32_t>((m_filter->radius() - 2.f * math::RayEpsilon<ScalarFloat>) * 2.f);

        Point2f base = lo - pos;
        for (uint32_t i = 0; i < n; ++i) {
            Point2f p = base + i;
            if constexpr (!is_cuda_array_v<Float>) {
                m_weights[i] = m_filter->eval_discretized(p.x(), active);
            } else {
                m_weights[i] = m_filter->eval(p.x(), active);
            }
        }

        // Float wx(0);
        // for (uint32_t i = 0; i < n; ++i) {
        //     wx += m_weights[i];
        // }

        // Float factor = rcp(wx);
        // for (uint32_t i = 0; i < n; ++i)
        //     m_weights[i] *= factor;

        ENOKI_NOUNROLL for (uint32_t tr = 0; tr < n; ++tr) {
            UInt32 x = lo.x() + tr;
            Mask enabled = active && x <= hi.x() && pos.y() <= size.y();

            UInt32 offset = m_channel_count * (x * size.y() + lo.y());
            Float weight = m_weights[tr];

            ENOKI_NOUNROLL for (uint32_t k = 0; k < m_channel_count; ++k) {
                scatter_add(m_data, value[k] * weight, offset + k, enabled);
                scatter_add(m_counts, UInt32(1), offset + k, enabled);
            }
        }
    } else {
        Point2u lo = ceil2int<Point2i>(pos - ScalarVector2f(.5f, 0.f));
        UInt32 offset = m_channel_count * (lo.x() * size.y() + lo.y());

        Mask enabled = active && all(lo >= 0u && lo < m_size);

        ENOKI_NOUNROLL for (uint32_t k = 0; k < m_channel_count; ++k) {
            scatter_add(m_data, value[k], offset + k, enabled);
            scatter_add(m_counts, UInt32(1), offset + k, enabled);
        }
    }

    return active;
};

MTS_VARIANT void Histogram<Float, Spectrum>::put(const Histogram *hist) {
    ScopedPhase sp(ProfilerPhase::HistogramPut);

    ScalarVector2i source_size = { hist->size().y(), hist->size().x() + 2 * hist->border_size() },
                   target_size = { size().y(), size().x() + 2 * border_size() };

    ScalarPoint2i source_offset = { hist->offset().y(), hist->offset().x() - hist->border_size() },
                  target_offset = { offset().y(), offset().x() - border_size() };

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

MTS_VARIANT std::string Histogram<Float, Spectrum>::to_string() const {
    std::ostringstream oss;
    oss << "Histogram[" << std::endl
        << "  bin_count = " << height() << "," << std::endl
        << "  time_step_count = " << width() << "," << std::endl
        << "  border_size = " << m_border_size;
    if (m_filter)
        oss << "," << std::endl << "  filter = " << string::indent(m_filter);
    oss << std::endl
        << "]";
    return oss.str();
}

MTS_IMPLEMENT_CLASS_VARIANT(Histogram, Object)
MTS_INSTANTIATE_CLASS(Histogram)
NAMESPACE_END(mitsuba)
