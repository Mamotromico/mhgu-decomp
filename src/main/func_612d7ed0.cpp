#include <stdint.h>

struct func_612d7ed0_obj {
    uint8_t pad[0x24];
    uint32_t field_24;
    uint32_t field_28;
};

extern "C" void func_612d7ed0(struct func_612d7ed0_obj *self, uint32_t a, uint32_t b)
{
    self->field_24 = a;
    self->field_28 = b;
}