#include <stdint.h>

struct Src {
    uint8_t b[6];
};

struct Dst {
    uint8_t pad0[0x1ac];
    uint8_t b[6];
};

extern "C" void func_6056140c(Dst *dst, const Src *src)
{
    dst->b[0] = src->b[0];
    dst->b[1] = src->b[1];
    dst->b[2] = src->b[2];
    dst->b[3] = src->b[3];
    dst->b[4] = src->b[4];
    dst->b[5] = src->b[5];
}