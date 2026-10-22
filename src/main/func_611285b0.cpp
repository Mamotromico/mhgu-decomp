struct Inner {
    unsigned char pad0[0x3c9];
    unsigned char value;
};

struct Outer {
    unsigned char pad0[0x3328];
    Inner *inner;
};

extern "C" unsigned int func_611285b0(Outer *outer) {
    return (outer->inner->value >> 4) & 1u;
}