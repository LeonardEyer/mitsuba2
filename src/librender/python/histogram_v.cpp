#include <mitsuba/python/python.h>
#include <mitsuba/render/histogram.h>


MTS_PY_EXPORT(Histogram) {
    MTS_PY_IMPORT_TYPES(Histogram)
    MTS_PY_CLASS(Histogram, Object)
        .def(py::init<const ScalarVector2u &, const size_t>(),
             "size"_a, "channel_count"_a = 1, D(Histogram))
        .def(py::init<const ScalarUInt32, const ScalarUInt32>(),
             "n_time_bins"_a, "n_wavelength_bins"_a, D(Histogram))
        .def("put",
             vectorize(py::overload_cast<const Point2f &,
                                         const Spectrum &, mask_t<Float>>(
                 &Histogram::put)),
             "pos"_a, "value"_a, "active"_a = true)
        .def("put", py::overload_cast<const Histogram *>(&Histogram::put),
             "hist"_a)
        .def_method(Histogram, clear)
        .def_method(Histogram, set_offset, "offset"_a)
        .def_method(Histogram, offset)
        .def_method(Histogram, size)
        .def_method(Histogram, width)
        .def_method(Histogram, height)
        .def("data", py::overload_cast<>(&Histogram::data, py::const_), D(Histogram, data))
        .def("counts", py::overload_cast<>(&Histogram::counts, py::const_), D(Histogram, counts));
}
