struct S {
    unsigned char pad0[0xb0];
    int field_b0;
    unsigned char field_b4;
};

extern "C" void func_60169d44(S *s, int a, unsigned char b) {
    s->field_b0 = a;
    s->field_b4 = b;
}