#include <stdint.h>

struct Func_613a5d14_Obj {
    uint8_t pad[0x18];
    uint64_t v;
};

extern "C" void func_613a5d14(struct Func_613a5d14_Obj *obj, uint32_t ignored, uint32_t lo, uint32_t hi) {
    (void)ignored;
    obj->v = ((uint64_t)hi << 32) | (uint64_t)lo;
}