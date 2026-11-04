#include <stdint.h>

struct Inner {
    uint32_t header;
    uint8_t pad0[0x2A78 - 4];
    uint32_t mask;
};

struct Table {
    Inner slot[15];
};

extern "C" uint32_t func_60524b98(Table *t, uint32_t a, uint32_t b)
{
    uint32_t idx = a - 7;
    if (idx > 0xE)
        return 0;
    uint32_t val = *(uint32_t *)((char *)t + idx * 0x80 + (b >> 5) * 4 + 0x2A78);
    return (val & (1u << (b & 0x1F))) ? 1 : 0;
}