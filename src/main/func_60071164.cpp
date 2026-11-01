#include <stdint.h>

struct Inner {
    uint8_t pad0[0x7c];
    uint32_t field7c;
    uint8_t pad80[0xfa - 0x80];
    uint8_t fieldfa;
};

extern "C" uint32_t func_60071164(uint8_t *base, uint32_t idx) {
    uint32_t off = 0x75ec;
    Inner *p = *(Inner **)(base + off);
    uint32_t v = p->field7c;
    if (v == 0)
        return 0;
    uint8_t b = p->fieldfa;
    uint32_t r = 0;
    if (b > idx)
        r = v + (idx << 4);
    return r;
}