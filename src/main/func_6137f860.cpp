#include <stdint.h>

struct src_6137f860 {
    uint8_t pad0[0x68];
    uint32_t field_0x68;
};

extern "C" void func_6137f860(uint32_t *dst, const struct src_6137f860 *src) {
    uint32_t value = 0x6c50;
    if (src->field_0x68 == 1)
        value = 0;
    *dst = value;
}