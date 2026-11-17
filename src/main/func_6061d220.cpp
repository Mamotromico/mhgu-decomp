#include <stdint.h>

struct In {
    uint32_t a;
    uint32_t b;
    uint32_t c;
};

struct Outer {
    uint8_t pad0[0x590];
    uint32_t bitmap;
    uint8_t pad1[0x5a0 - 0x594];
    uint8_t entries[1];
};

struct Entry {
    uint32_t x;
    uint32_t y;
    uint32_t z;
    uint8_t pad0[0x10 - 0x0c];
    uint8_t f0;
    uint8_t f1;
    uint8_t f2;
    uint8_t pad1;
    uint32_t f4;
};

extern "C" int func_6061d220(Outer *self, const In *in, uint8_t val, unsigned idx)
{
    unsigned bit = 1u << idx;
    if (self->bitmap & bit)
        return 0;

    self->bitmap = self->bitmap | bit;

    Entry *e = (Entry *)((uint8_t *)self + 0x5a0 + (idx << 5));
    e->x = in->a;
    e->y = in->b;
    e->z = in->c;
    e->f0 = val;
    e->f1 = 0;
    e->f2 = (uint8_t)(e->f2 & 0xf8);
    e->f4 = 0;
    return 1;
}