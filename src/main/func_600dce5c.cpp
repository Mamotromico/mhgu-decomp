#include <stdint.h>

struct func_600dce5c_s {
    uint8_t pad0[4];
    uint16_t field4;
    uint8_t pad6[0x18];
    uint8_t field1e;
};

extern "C" int func_600dce5c(const func_600dce5c_s *p)
{
    return ((p->field4 & 0x1f) == 0x14) ? p->field1e : 0;
}