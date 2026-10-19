#include <stdint.h>

struct Func600dcc58Struct {
    uint8_t pad0[4];
    uint16_t field_4;
    uint8_t pad1[0x1f];
    uint8_t field_25;
};

extern "C" void func_600dcc58(Func600dcc58Struct *p, uint8_t value) {
    if ((p->field_4 & 0x1f) == 0x14) {
        p->field_25 = value;
    }
}