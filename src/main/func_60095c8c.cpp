#include <stdint.h>

struct S_60095c8c {
    uint8_t pad[0x1404];
    uint16_t field;
};

extern "C" int func_60095c8c(const S_60095c8c *s) {
    return (s->field & 0x440) != 0;
}