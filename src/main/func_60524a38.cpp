#include <stdint.h>

struct S {
    char pad0[0x360 * 5];
};

extern "C" void func_60524a38(struct S *base, int idx, unsigned bit);

extern "C" void func_60524a38(struct S *base, int idx, unsigned bit)
{
    int i = idx - 1;
    if ((unsigned)i <= 4) {
        char *p = (char *)base + i * 0x360;
        unsigned word_idx = bit >> 5;
        unsigned bit_idx = bit & 0x1f;
        unsigned *addr = (unsigned *)(p + word_idx * 4 + 0x1908);
        *addr &= ~(1u << bit_idx);
    }
}