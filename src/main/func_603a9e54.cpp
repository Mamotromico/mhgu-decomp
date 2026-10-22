#include <stdint.h>

struct func_603a9e54_inner {
    uint8_t pad0[0x30];
    uint32_t value;
};

struct func_603a9e54_outer {
    uint8_t pad0[0xa4];
    struct func_603a9e54_inner *inner;
};

extern "C" uint32_t func_603a9e54(struct func_603a9e54_outer *p)
{
    struct func_603a9e54_inner *inner = p->inner;
    return inner ? inner->value : 0;
}