#include <stdint.h>

struct func_61228b94_s {
    uint16_t a;
    uint16_t b : 11;
};

extern "C" uint16_t func_61228b94(const struct func_61228b94_s *p)
{
    return p->b;
}