struct inner_60071444 {
    unsigned char pad0[0xb8];
    unsigned char field;
};

struct outer_60071444 {
    unsigned char pad0[0x75e8];
    struct inner_60071444 *inner;
};

extern "C" unsigned char func_60071444(struct outer_60071444 *p) {
    return p->inner->field;
}