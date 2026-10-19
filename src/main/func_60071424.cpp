struct inner_60071424 {
    char pad0[0xb4];
    int value;
};

struct outer_60071424 {
    char pad0[0x75e8];
    inner_60071424 *inner;
};

extern "C" int func_60071424(outer_60071424 *outer) {
    return outer->inner->value;
}