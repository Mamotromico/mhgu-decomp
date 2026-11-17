#include <stdint.h>

struct S {
    char pad0[0x484];
    uint8_t field484;
    uint8_t field485;
    char pad2[0x488 - 0x486];
    uint32_t field488;
};

extern "C" int func_60870f68(struct S *p)
{
    int result = 0;
    if (p->field484 == 0) {
        if (p->field485 == 0)
            return result;
        result = p->field488;
        if (result != 0)
            result = 1;
    }
    return result;
}