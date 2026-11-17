extern "C" bool func_6086ebc8(char *p);

namespace nn { namespace hid {
struct VibrationPlayer {
    bool IsPlaying() const;
};
}}

extern "C" bool func_6086ebc8(char *p) {
    return reinterpret_cast<nn::hid::VibrationPlayer *>(p + 0x28)->IsPlaying();
}