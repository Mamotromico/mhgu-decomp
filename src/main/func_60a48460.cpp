struct A {
    unsigned char pad_0[0x68];
    void *field_68;
};

struct B {
    unsigned char pad_0[0x70];
    void *field_70;
};

extern "C" void func_60a48460(A *a, B *b) {
    a->field_68 = b;
    if (b != 0) {
        b->field_70 = a;
    }
}