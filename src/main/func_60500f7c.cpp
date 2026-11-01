#include <stdint.h>

struct Data_60500f7c {
    uint8_t padding[0x1a0];
    uint16_t bits;
};

extern "C" int func_60500f7c(const Data_60500f7c *self, int bit)
{
    return (self->bits & (1u << (bit - 0x32))) != 0;
}