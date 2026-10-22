struct Inner {
    char pad0[0x14c];
    unsigned int value;
};

struct B {
    char pad0[0x24];
    struct Inner *inner;
};

struct A {
    char pad0[8];
    struct B *b;
    char pad1[0x24];
    unsigned int value;
};

extern "C" void func_601b9094(struct A *a, struct B *b) {
    a->b = b;
    a->value = b->inner->value;
}