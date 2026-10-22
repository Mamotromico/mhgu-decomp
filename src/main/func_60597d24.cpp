struct S60597d24 {
    char pad_0[0x4c];
    unsigned int field_4c;
    char pad_50[0x4];
    unsigned int field_54;
};

extern "C" void func_60597d24(S60597d24* p, unsigned int value) {
    p->field_54 |= 1u;
    p->field_4c = value;
}