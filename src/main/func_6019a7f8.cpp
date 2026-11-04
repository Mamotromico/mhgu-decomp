#include <stdint.h>

extern "C" int func_6019a7f8(const uint8_t *base, unsigned index)
{
    if (index > 0x17)
        return 0;

    const uint8_t *p = base + (index * 0xaa + 0x6320);

    for (unsigned i = 0; i < 0x20; i++) {
        uint16_t lo = *(const uint16_t *)(p - 2);
        uint16_t hi = *(const uint16_t *)p;
        if (lo != 0 && hi != 0)
            return 1;
        p += 4;
    }
    return 0;
}