#include <stdint.h>

struct func_600dcbbc_s {
    uint8_t pad_0[4];
    uint16_t field_4;
    uint8_t pad_6[0x11 - 0x6];
    uint8_t field_11;
};

extern "C" int func_600dcbbc(const func_600dcbbc_s *p)
{
    unsigned short v = p->field_4;
    int result = 0;

    if ((v & 0x1f) == 0x14)
        result = p->field_11;

    return result;
}