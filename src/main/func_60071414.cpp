struct Inner {
    unsigned char pad[0xc1];
    unsigned char value;
};

struct Outer {
    unsigned char pad[0x75e8];
    struct Inner *inner;
};

extern "C" unsigned char func_60071414(struct Outer *p) {
    return p->inner->value;
}