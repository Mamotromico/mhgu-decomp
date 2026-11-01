#include <stdint.h>

struct S {
    uint8_t pad0[0x55];
    uint8_t field55;
};

extern "C" uint16_t func_603abb14(S *s, uint32_t idx);

extern "C" uint16_t func_603abb14(S *s, uint32_t idx) {
    if (idx > 2)
        return 0;
    if (s->field55 != 0)
        return 0;
    return *(uint16_t *)((uint8_t *)s + idx * 2 + 0x1660);
}