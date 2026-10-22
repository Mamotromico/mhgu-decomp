#include <stdint.h>

struct Data {
    uint8_t pad0[0x54];
    uint32_t field54;
    uint8_t pad1[0x74 - 0x58];
    uint32_t field74;
};

extern "C" void func_6057348c(Data *p, uint32_t v)
{
    p->field74 |= 0x4;
    p->field54 = v;
}