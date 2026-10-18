#include <stdint.h>

struct inner_605bc0e8 {
    char pad[0x58];
    void *field;
};

struct outer_605bc0e8 {
    char pad[0x9c];
    struct inner_605bc0e8 *ptr;
};

extern "C" void *func_605bc0e8(struct outer_605bc0e8 *obj, void *value)
{
    struct inner_605bc0e8 *inner = obj->ptr;
    inner->field = value;
    return inner;
}