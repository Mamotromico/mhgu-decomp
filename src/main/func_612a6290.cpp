#include <cstdint>

struct S {
    char pad[0x34];
    uint16_t field;
};

extern "C" void func_612a6290(S *s, uint16_t v) {
    s->field = v;
}