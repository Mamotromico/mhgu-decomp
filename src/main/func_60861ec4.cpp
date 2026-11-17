namespace nn { namespace swkbd {
struct KeyboardConfig;
enum Preset { };
int MakePreset(KeyboardConfig*, Preset);
} }

extern "C" int func_60861ec4(char* p, int preset) {
    return nn::swkbd::MakePreset((nn::swkbd::KeyboardConfig*)(p + 4), (nn::swkbd::Preset)preset);
}