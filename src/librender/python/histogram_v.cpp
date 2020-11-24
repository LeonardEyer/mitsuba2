#include <mitsuba/render/histogram.h>
#include <mitsuba/python/python.h>

MTS_PY_EXPORT(Histogram) {
    MTS_PY_IMPORT_TYPES(Histogram)
    MTS_PY_CLASS(Histogram, Object)
        .def(py::init<size_t, size_t, ScalarPoint2f, ScalarPoint2f>(), "bin_count"_a, "time_step_count"_a, "wav_range"_a, "time_range"_a)
        .def("put", vectorize(py::overload_cast<const Float &, const Wavelength &, const Spectrum &,mask_t<Float>>(&Histogram::put)),
             "time_step"_a, "wavelengths"_a,"value"_a, "active"_a = true,
             D(Histogram, put))
        .def_method(Histogram, clear)
        .def_method(Histogram, bin_count)
        .def_method(Histogram, time_step_count)
        .def_method(Histogram, wav_range)
        .def_method(Histogram, time_range)
        .def("data", py::overload_cast<>(&Histogram::data, py::const_), D(Histogram, data));
        ;
}