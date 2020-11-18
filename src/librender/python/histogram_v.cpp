#include <mitsuba/render/histogram.h>
#include <mitsuba/python/python.h>

MTS_PY_EXPORT(Histogram) {
    MTS_PY_IMPORT_TYPES(Histogram)
    MTS_PY_CLASS(Histogram, Object)
        .def(py::init<int, int>(), "channel_count"_a, "time_step_count"_a)
        .def("put", vectorize(py::overload_cast<const UInt32 &, const Spectrum &,mask_t<Float>>(&Histogram::put)),
             "time_step"_a, "value"_a, "active"_a = true,
             D(Histogram, put))
        .def_method(Histogram, clear)
        .def_method(Histogram, channel_count)
        .def_method(Histogram, time_step_count)
        .def("data", py::overload_cast<>(&Histogram::data, py::const_), D(Histogram, data));
        ;
}