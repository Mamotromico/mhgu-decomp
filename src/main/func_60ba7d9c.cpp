#include <stdint.h>

struct S {
    uint8_t padding[0x34];
    uint32_t field;
};

extern "C" int func_60ba7d9c(const S *s) {
    uint32_t v = s->field - 3u;
    return v < 2u;
}