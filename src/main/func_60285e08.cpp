#include <stdint.h>

extern "C" void func_60285e08(uint8_t *base, uint32_t bit)
{
    uint32_t idx = bit >> 5;
    uint32_t mask = 1u << (bit & 0x1f);
    uint32_t *p = (uint32_t *)(base + idx * 4 + 0x1414);
    *p = *p & ~mask;
}