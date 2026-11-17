#include <stdint.h>

struct Header {
    uint32_t w0;
    uint32_t w1;
    uint32_t w2;
    uint32_t w3;
    uint32_t w4;
};

struct Big {
    char pad0[0x30];
    struct Header h;
    char pad1[0x44 - 0x30 - 20];
    uint32_t a;
    uint32_t b;
};

extern "C" int func_60277400(const struct Big *p)
{
    struct Header h = p->h;
    uint32_t a = p->a;
    uint32_t b = p->b;

    int n = 0;
    n += (h.w0 != 0);
    n += (h.w1 != 0);
    n += (h.w2 != 0);
    n += (h.w3 != 0);
    n += (h.w4 != 0);
    n += (a != 0);
    n += (b != 0);
    return n;
}