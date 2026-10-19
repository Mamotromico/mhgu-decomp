#include <stdint.h>

struct S {
    uint8_t pad0[4];
    uint16_t field4;
    uint8_t pad1[0xD];
    uint8_t field13;
};

extern "C" void func_600dcda8(struct S *s, uint8_t val)
{
    if ((s->field4 & 0x1f) == 0x14)
        s->field13 = val;
}