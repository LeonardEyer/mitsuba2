#include <mitsuba/core/bitmap.h>
#include <mitsuba/core/filesystem.h>
#include <mitsuba/core/fstream.h>
#include <mitsuba/core/spectrum.h>
#include <mitsuba/core/string.h>
#include <mitsuba/render/film.h>
#include <mitsuba/render/fwd.h>
#include <mitsuba/render/imageblock.h>
#include <mitsuba/render/histogram.h>

NAMESPACE_BEGIN(mitsuba)

template <typename Float, typename Spectrum>
class Tape final : public Film<Float, Spectrum> {
public:
    MTS_IMPORT_BASE(Film, m_size)
    MTS_IMPORT_TYPES(ImageBlock, Histogram)

    Tape(const Properties &props) : Base(props) {

        // Update size
        m_size = ScalarVector2i(props.int_("time_steps", 1), 1);

        m_max_time = props.float_("max_time", 1.f);
    }

    void prepare(const std::vector<std::string> &channels) override {
        Throw("Tape wont work with typical channels. We expect floating point wavelength bins");
    }

    void prepare(const std::vector<ScalarFloat> &wavelength_bins) override {

        m_size.y() = wavelength_bins.size();

        // Create histogram
        m_storage =
            new Histogram(m_size.x(), { 0, m_max_time }, wavelength_bins);
        // prepare it
        m_storage->clear();
    }

    void put(const ImageBlock *block) override {
        NotImplementedError("put ImageBlock");
    }

    void put(const Histogram *hist) override {
        m_storage->put(hist);
    }

    void develop() override { NotImplementedError("develop"); }

    bool develop(const ScalarPoint2i &offset, const ScalarVector2i &size,
                 const ScalarPoint2i &target_offset,
                 Bitmap *target) const override {
        NotImplementedError("develop");
    }

    ref<Bitmap> bitmap(bool raw = false) override {

        if constexpr (is_cuda_array_v<Float>) {
            cuda_eval();
            cuda_sync();
        }

        ref<Bitmap> source = new Bitmap(Bitmap::PixelFormat::Y,
                                        struct_type_v<ScalarFloat>, m_storage->size(), 1,
                                        (uint8_t *) m_storage->data().managed().data());

        //if (raw)
        return source;
    }

    DynamicBuffer<Float> &raw() override {
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
    ScalarFloat m_max_time;
    ref<Histogram> m_storage;
    std::vector<ScalarFloat> m_wavelength_bins;
};

MTS_IMPLEMENT_CLASS_VARIANT(Tape, Film)
MTS_EXPORT_PLUGIN(Tape, "Tape")
NAMESPACE_END(mitsuba)
