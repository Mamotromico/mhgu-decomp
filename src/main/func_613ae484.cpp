struct Inner {
    unsigned char pad0[0x2b8];
    int value;
};

struct Outer {
    unsigned char pad1[0x2c];
    Inner *inner;
};

extern "C" int func_613ae484(Outer *p) {
    return p->inner->value;
}