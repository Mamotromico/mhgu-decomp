#include <stdint.h>

struct func_60b49c1c_s {
    uint8_t pad[0x21e];
    uint16_t value;
};

extern "C" uint16_t func_60b49c1c(const struct func_60b49c1c_s *p)
{
    return p->value;
}