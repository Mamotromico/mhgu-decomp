#include <stdint.h>

struct func_60573ad8_entry {
    uint32_t pad[0x1e];
    uint32_t value;
};

extern "C" uint32_t func_60573ad8(uint32_t *base, uint32_t index)
{
    return ((struct func_60573ad8_entry *)(base + index))->value;
}