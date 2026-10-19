#include <stdint.h>

struct Data_60c175fc {
    uint8_t pad_0[0x58];
    uint32_t field_58;
    uint8_t pad_5c[0x30];
    uint32_t field_8c;
    uint32_t field_90;
};

extern "C" void func_60c175fc(Data_60c175fc *p, uint32_t a, uint32_t b, uint32_t c)
{
    p->field_58 = a;
    p->field_8c = b;
    p->field_90 = c;
}