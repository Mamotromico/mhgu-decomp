#include <cstdint>

struct S {
    uint8_t pad0[0xa8];
    int32_t field_a8;
    uint8_t pad1[0xbc - 0xa8 - 4];
    int32_t field_bc;
};

extern "C" int func_6137eb70(S* s)
{
    int result = 0;
    if (s->field_bc != 1)
        return result;
    int v = s->field_a8;
    uint32_t t = (uint32_t)v - 2u;
    result = 0;
    if (t < 3u)
        result = 1;
    return result;
}