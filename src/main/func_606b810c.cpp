#include <stdint.h>

struct Data_606b810c {
    uint8_t pad_0x00[0x4c];
    uint32_t field_0x4c;
    uint32_t field_0x50;
};

extern "C" void func_606b810c(Data_606b810c* self, uint32_t value) {
    self->field_0x4c |= 1u;
    self->field_0x50 = value;
}