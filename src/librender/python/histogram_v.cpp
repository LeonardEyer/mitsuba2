#include <mitsuba/python/python.h>
#include <mitsuba/render/histogram.h>

MTS_PY_EXPORT(Histogram) {
    MTS_PY_IMPORT_TYPES(Histogram)
    MTS_PY_CLASS(Histogram, Object)
        .def(py::init<size_t, const ScalarPoint2f &,
                      const std::vector<float> &>(),
             "time_step_count"_a, "time_range"_a, "wavelength_bins"_a,
             D(Histogram))
        .def("put",
             vectorize(py::overload_cast<const Float &, const Wavelength &,
                                         const Spectrum &, mask_t<Float>>(
                 &Histogram::put)),
             "time_step"_a, "wavelengths"_a, "value"_a, "active"_a = true)
        .def("put", py::overload_cast<const Histogram *>(&Histogram::put),
             "hist"_a)
        .def_method(Histogram, clear)
        .def_method(Histogram, bin_count)
        .def_method(Histogram, time_step_count)
        .def_method(Histogram, set_offset, "offset"_a)
        .def_method(Histogram, offset)
        .def_method(Histogram, size)
        .def_method(Histogram, width)
        .def_method(Histogram, height)
        .def_method(Histogram, wav_range)
        .def_method(Histogram, time_range)
        .def_method(Histogram, wavelength_bins)
        .def("data", py::overload_cast<>(&Histogram::data, py::const_), D(Histogram, data))
        .def("counts", py::overload_cast<>(&Histogram::counts, py::const_), D(Histogram, counts))
    ;
}