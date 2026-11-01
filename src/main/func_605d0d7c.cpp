#include <cstdint>

struct S {
    uint8_t pad00[0x50];
    uint32_t field50;
    uint8_t pad54[0x08];
    uint32_t arr5c[1];      // offset 0x5c
    uint8_t pad60[0x0e];
    uint8_t field6e;
};

extern "C" void func_605d0d7c(S *s, uint32_t index, uint32_t value)
{
    if (index > 2)
        return;
    s->field50 |= 0x8;
    *reinterpret_cast<uint32_t *>(reinterpret_cast<uint8_t *>(s) + 0x5c + index * 4) = value;
    s->field6e = 1;
}