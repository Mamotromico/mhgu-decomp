struct inner_t {
    char pad0[0x5e09];
    unsigned char field;
};

struct outer_t {
    char pad0[0x1428];
    inner_t *inner;
};

extern "C" inner_t *func_600a1fe4(outer_t *outer)
{
    inner_t *inner = outer->inner;
    inner->field = 0;
    return inner;
}