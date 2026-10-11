#include <stdint.h>

typedef struct {
    uint8_t pad[0x18];
    uint64_t value;
} func_608103b8_arg;

extern "C" uint64_t func_608103b8(const func_608103b8_arg *arg)
{
    return arg->value;
}