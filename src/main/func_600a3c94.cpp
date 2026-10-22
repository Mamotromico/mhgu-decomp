extern "C" void func_600a3c94(struct Outer *, unsigned int);

struct Inner {
    unsigned char pad0[0x3b4];
    unsigned short field;
};

struct Outer {
    unsigned char pad0[0x1428];
    struct Inner *inner;
};

extern "C" void func_600a3c94(struct Outer *outer, unsigned int value) {
    struct Inner *inner = outer->inner;
    inner->field |= value;
}