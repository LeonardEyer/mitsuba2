#include <mitsuba/core/bitmap.h>
#include <mitsuba/core/filesystem.h>
#include <mitsuba/core/fstream.h>
#include <mitsuba/core/spectrum.h>
#include <mitsuba/core/string.h>
#include <mitsuba/render/film.h>
#include <mitsuba/render/fwd.h>
#include <mitsuba/render/histogram.h>
#include <mitsuba/render/imageblock.h>

NAMESPACE_BEGIN(mitsuba)

template <typename Float, typename Spectrum>
class Tape final : public Film<Float, Spectrum> {
public:
    MTS_IMPORT_BASE(Film, m_size)
    MTS_IMPORT_TYPES(ImageBlock, Histogram)

    Tape(const Properties &props) : Base(props) {

        // Update size
        m_size = ScalarVector2i(
            props.int_("time_steps", 1),
            props.int_("wav_bins", 1)
        );

        // Create histogram
        m_storage = new Histogram(m_size, 1);
        // prepare it
        m_storage->clear();
    }

    void prepare(const std::vector<std::string> &channels) override {
        Throw("Tape wont work with typical channels. We expect floating point "
              "wavelength bins");
    }

    void prepare(const std::vector<ScalarFloat> &wavelength_bins) override {

    }

    void put(const ImageBlock *block) override {
        NotImplementedError("put ImageBlock");
    }

    void put(const Histogram *hist) override { m_storage->put(hist); }

    void develop() override { NotImplementedError("develop"); }

    bool develop(const ScalarPoint2i &offset, const ScalarVector2i &size,
                 const ScalarPoint2i &target_offset,
                 Bitmap *target) const override {
        NotImplementedError("develop");
    }

    ref<Histogram> get_histogram() override { return m_storage; }

    ref<Bitmap> bitmap(bool raw = false) override {

        if constexpr (is_cuda_array_v<Float>) {
            cuda_eval();
            cuda_sync();
        }

//        DynamicBuffer<Float> tmp =
//            raw ? m_storage->data() : m_storage->data() / m_storage->counts();

//        ref<Bitmap> source = new Bitmap(Bitmap::PixelFormat::Y, struct_type_v<ScalarUInt32>,
//                                        m_storage->size(), 1, (uint8_t *) m_storage->counts().managed().data());

        ref<Bitmap> source;

        if (raw)
            source = new Bitmap(Bitmap::PixelFormat::Y, struct_type_v<ScalarFloat>,
                           m_storage->size(), m_storage->channel_count(), (uint8_t *) m_storage->data().managed().data());
        else
            source = new Bitmap(Bitmap::PixelFormat::Y, struct_type_v<ScalarFloat>,
                       m_storage->size(), m_storage->channel_count(), (uint8_t *) m_storage->counts().managed().data());

        return source;
    }

    void set_destination_file(const fs::path &filename) override {
        NotImplementedError("set_destination_file");
    }

    bool destination_exists(const fs::path &basename) const override {
        NotImplementedError("destination_exists");
    }

    std::string to_string() const override {
        std::ostringstream oss;
        oss << "Tape[" << std::endl
            << "  size = " << m_size << "," << std::endl
            << "]";
        return oss.str();
    }

    MTS_DECLARE_CLASS()
protected:
    ref<Histogram> m_storage;
};

MTS_IMPLEMENT_CLASS_VARIANT(Tape, Film)
MTS_EXPORT_PLUGIN(Tape, "Tape")
NAMESPACE_END(mitsuba)
