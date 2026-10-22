struct Inner {
    char pad0[0x14c];
    unsigned int value;
};

struct Middle {
    char pad0[0x24];
    struct Inner *inner;
};

struct Outer {
    char pad0[0x10];
    struct Middle *middle;
    char pad1[0x2c];
    unsigned int value;
};

extern "C" void func_601b8338(struct Outer *r0, struct Middle *r1) {
    r0->middle = r1;
    r0->value = r1->inner->value;
}