#include <stdint.h>

struct S {
    uint8_t pad0[0x4c];
    volatile uint32_t field_4c;
    uint8_t pad1[0x58 - 0x50];
    volatile uint32_t field_58;
};

extern "C" void func_60565d4c(volatile S *s, uint32_t v) {
    s->field_58 = v;
    s->field_4c |= 4;
}