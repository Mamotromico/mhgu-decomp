struct S0 {
    int field_0x0;
};

struct S1 {
    unsigned char pad_0x0[0x10];
    int field_0x10;
};

extern "C" void func_61306fcc(struct S0 *p0, struct S1 *p1, int value) {
    p1->field_0x10 = value;
    p0->field_0x0 = 0;
}