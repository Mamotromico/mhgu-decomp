struct S0 {
    int field_0;
};

struct S1 {
    unsigned char pad[0x18];
    unsigned char field_18;
};

extern "C" void func_6139fae8(S0 *a, S1 *b) {
    b->field_18 = 0;
    a->field_0 = 0;
}