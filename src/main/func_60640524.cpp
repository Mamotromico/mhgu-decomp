#include <stdint.h>

struct Data_60640524 {
    uint8_t pad_00[0x4c];
    uint32_t field_4c;
    uint8_t pad_50[0x04];
    uint8_t bytes_54[4];
};

extern "C" void func_60640524(Data_60640524 *p, unsigned int index, uint8_t value)
{
    if (index > 3u)
        return;
    p->field_4c |= 0x8u;
    p->bytes_54[index] = value;
}