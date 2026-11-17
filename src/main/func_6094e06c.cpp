#include <stdint.h>

struct Src {
    uint32_t a;
    uint32_t b;
    uint32_t c;
};

struct Dst {
    char pad0[0x40];
    uint32_t x;
    uint32_t y;
    uint32_t z;
    uint32_t w;
};

extern "C" void func_6094e06c(Dst *d, const Src *s)
{
    uint32_t a = s->a;
    uint32_t b = s->b;
    uint32_t c = s->c;
    d->x = a;
    d->y = b;
    d->z = c;
    d->w = 0x3f800000u;
}