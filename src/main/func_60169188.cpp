#include <stdint.h>

struct Layout_60169188 {
    uint8_t pad_0x00[0x30];
    uint32_t field_0x30;
    uint8_t pad_0x34[0x58];
    uint32_t field_0x8c;
};

extern "C" void func_60169188(Layout_60169188 *p, uint32_t value)
{
    p->field_0x30 |= 0x800000u;
    p->field_0x8c = value;
}