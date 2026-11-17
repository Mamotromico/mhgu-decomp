#include <stdint.h>

struct Src {
    uint8_t pad0[0x40];
    uint32_t data[16];
};

extern "C" int func_60c18038(char *dst, char *src, uint32_t *in, char r3)
{
    uint32_t *p54 = *(uint32_t **)(src + 0x54);
    int ret = 0;
    if (p54 != 0) {
        if (*(uint8_t *)(src + 5) != 0) {
            uint32_t *d = (uint32_t *)dst;
            d[1] = (uint32_t)(uintptr_t)src;
            ret = 1;
            for (int i = 0; i < 16; i++) {
                d[4 + i] = in[i];
            }
            *(uint8_t *)(dst + 8) = (uint8_t)r3;
        }
    }
    return ret;
}