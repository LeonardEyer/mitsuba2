#include <mitsuba/core/spectrum.h>
#include <mitsuba/core/string.h>
#include <mitsuba/render/film.h>
#include <mitsuba/render/fwd.h>
#include <mitsuba/render/histogram.h>

NAMESPACE_BEGIN(mitsuba)

template <typename Float, typename Spectrum>
class Tape final : public Film<Float, Spectrum> {
public:
    MTS_IMPORT_BASE(Film, m_size, m_filter)
    MTS_IMPORT_TYPES(ImageBlock, Histogram)

    Tape(const Properties &props) : Base(props) { }

    void prepare(const std::vector<std::string> &channels) override {
        m_storage = new Histogram(10, {0, 10}, {0, 10});
        m_storage->clear();
    }

    void put(const ImageBlock *block) override {
        NotImplementedError("put ImageBlock");
    }

    void put(const Histogram *hist) override {
        m_storage->put(hist);
    }

    void develop() override {
        NotImplementedError("develop");
    }

    bool develop(
        const ScalarPoint2i  &offset,
        const ScalarVector2i &size,
        const ScalarPoint2i  &target_offset,
        Bitmap *target) const override {
        NotImplementedError("develop");
    }

    ref<Bitmap> bitmap(bool raw = false) override {
        NotImplementedError("bitmap");
    }

    DynamicBuffer<Float> &raw() override{
       return m_storage->data();
    }

    void set_destination_file(const fs::path &filename) override {
        NotImplementedError("set_destination_file");
    }

    bool destination_exists(const fs::path &basename) const override {
        NotImplementedError("destination_exists");
    }

    MTS_DECLARE_CLASS()
    protected:
    ref<Histogram> m_storage;
};

MTS_IMPLEMENT_CLASS_VARIANT(Tape, Film)
MTS_EXPORT_PLUGIN(Tape, "Tape")
NAMESPACE_END(mitsuba)
