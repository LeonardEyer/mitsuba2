#include <mitsuba/render/histogram.h>

NAMESPACE_BEGIN(mitsuba)

MTS_VARIANT std::string Histogram<Float, Spectrum>::to_string() const {
    std::ostringstream oss;
    oss << "Histogram[" << std::endl
        << "]";
    return oss.str();
}

MTS_IMPLEMENT_CLASS_VARIANT(Histogram, Object)
MTS_INSTANTIATE_CLASS(Histogram)
NAMESPACE_END(mitsuba)
