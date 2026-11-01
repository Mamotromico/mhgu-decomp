struct InnerA {
    unsigned char pad[0x249];
    unsigned char field_249;
};

struct InnerB {
    unsigned char pad[0x78];
    unsigned int field_78;
};

struct Outer {
    unsigned char pad0[0x1428];
    struct InnerA *a;
    unsigned char pad1[0x61c0];
    struct InnerB *b;
};

extern "C" unsigned int func_60071144(struct Outer *p) {
    struct InnerA *a = p->a;
    struct InnerB *b = p->b;
    return (a->field_249 << 5) + b->field_78;
}