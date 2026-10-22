struct B;

struct A {
    char pad_0x00[0x14];
    B *field_0x14;
};

struct B {
    char pad_0x00[0x4c];
    unsigned char field_0x4c;
};

extern "C" void func_601b834c(A *a, B *b) {
    a->field_0x14 = b;
    if (b != 0) {
        b->field_0x4c = 0xb;
    }
}