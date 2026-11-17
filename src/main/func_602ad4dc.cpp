#include <stdint.h>

struct S {
    char pad[0x2b70];
    uint64_t field;
};

extern "C" void func_602ad4dc(struct S *s) {
    uint32_t v = (uint32_t)s->field;
    v &= ~(0x3Fu << 16);
    s->field = v;  // high 32 bits become 0
}