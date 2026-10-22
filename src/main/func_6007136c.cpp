#include <stdint.h>

struct Inner {
    uint8_t pad_0[0x74];
    uint32_t value;              // offset 0x74
    uint8_t pad_78[0xc3 - 0x78]; // padding up to 0xc3
    uint8_t flag;                // offset 0xc3
};

struct Outer {
    uint8_t pad_0[0x75e8];
    Inner* inner;                // offset 0x75e8
};

extern "C" unsigned int func_6007136c(Outer* outer) {
    Inner* inner = outer->inner;
    if (inner->flag != 0) {
        return inner->value;
    }
    return 0;
}