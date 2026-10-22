struct Inner6112871c {
    char pad0[0x3c8];
    unsigned int field;
};

struct Outer6112871c {
    char pad0[0x3328];
    Inner6112871c *inner;
};

extern "C" unsigned int func_6112871c(Outer6112871c *outer) {
    return outer->inner->field & 1u;
}