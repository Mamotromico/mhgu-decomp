#include <stdint.h>

struct S {
    uint8_t pad0[4];
    uint8_t b4;
    uint8_t pad5[3];
    int32_t f8;
    uint8_t bc;
    uint8_t pad_d[3];
    int32_t f10;
    int32_t f14;
    int32_t f18;
    uint8_t pad1c[9];
    uint8_t f25;
    uint8_t f26;
};

extern "C" void func_6121b454(S *s) {
    s->bc = 0;
    s->b4 = 0;
    s->f10 = 0;
    s->f8 = -1;
    s->f14 = 0;
    s->f18 = 0;
    s->f25 = 0;
    s->f26 = 0xff;
}