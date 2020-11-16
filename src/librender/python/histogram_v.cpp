#include <mitsuba/render/histogram.h>
#include <mitsuba/python/python.h>

MTS_PY_EXPORT(Histogram) {
    MTS_PY_IMPORT_TYPES(Histogram)
    MTS_PY_CLASS(Histogram, Object)
        .def(py::init());
}