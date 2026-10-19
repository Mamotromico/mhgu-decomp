struct Inner_600bd4a8 {
    char pad0[0x5ac];
    unsigned char value;
};

struct Outer_600bd4a8 {
    char pad0[0x1428];
    struct Inner_600bd4a8 *inner;
};

extern "C" void func_600bd4a8(struct Outer_600bd4a8 *outer) {
    outer->inner->value = 1;
}