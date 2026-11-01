#include <stdint.h>

struct Struct_600daf90 {
    uint8_t pad0[4];
    uint16_t field_4;
    uint8_t pad1[0xa];
    uint32_t field_10;
};

extern "C" void func_600daf90(Struct_600daf90 *p, uint32_t value)
{
    uint16_t v = p->field_4 & 0x1f;
    if (v != 0xd && v != 0xb)
        return;
    p->field_10 |= value;
}