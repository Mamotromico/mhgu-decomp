struct Inner {
    unsigned char pad[0x5c90];
    int value;
};

struct Outer {
    unsigned char pad[0x1428];
    Inner *inner;
};

extern "C" int func_600c03f0(Outer *p) {
    return (p->inner->value > 0) ? 1 : 0;
}