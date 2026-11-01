#include <cstdint>

struct S {
    uint8_t pad0[0x2c];
    uint8_t *ptr;      // +0x2c
    uint32_t cap;      // +0x30
    uint32_t len;      // +0x34
};

extern "C" void func_6080d3c8(S *s, uint8_t val)
{
    uint32_t l = s->len;
    uint32_t cap = s->cap;
    uint32_t n = l + 1;
    if (n > cap)
        return;
    s->ptr[l] = val;
    s->len = s->len + 1;
}