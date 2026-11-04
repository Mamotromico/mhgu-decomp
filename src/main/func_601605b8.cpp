#include <cstdint>

struct S {
    uint8_t pad0[0x2c];
    uint32_t f_2c;
    uint8_t pad_30[0x30 - 0x2c - 4];
    uint8_t f_30;
    uint8_t pad_31[0x34 - 0x30 - 1];
    uint32_t f_34;
    uint8_t pad_38[0x38 - 0x34 - 4];
    uint8_t f_38;
    uint8_t pad_39[0x3c - 0x38 - 1];
    uint32_t f_3c;
    uint8_t pad_40[0x40 - 0x3c - 4];
    uint8_t f_40;
    uint8_t pad_41[0x44 - 0x40 - 1];
    uint32_t f_44;
    uint8_t pad_48[0x48 - 0x44 - 4];
    uint8_t f_48;
    uint8_t pad_49[0x4d - 0x48 - 1];
    uint8_t f_4d;
    uint8_t f_4e;
    uint8_t f_4f;
    uint8_t pad_50[0x54 - 0x4f - 1];
    uint32_t f_54;
};

extern "C" void func_601605b8(S* s, uint32_t v) {
    if (s->f_54 == v) return;
    s->f_54 = v;
    s->f_4d = 2;
    s->f_4e = 0;
    s->f_4f = 0;
    if (s->f_2c) s->f_30 = 1;
    if (s->f_34) s->f_38 = 1;
    if (s->f_3c) s->f_40 = 1;
    if (s->f_44) s->f_48 = 1;
}