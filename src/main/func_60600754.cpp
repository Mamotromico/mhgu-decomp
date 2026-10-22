struct S {
    char pad_0[0x58];
    unsigned int field_58;
    char pad_5c[0x08];
    unsigned int field_64;
};

extern "C" void func_60600754(S *s, unsigned int value) {
    s->field_64 |= 4u;
    s->field_58 = value;
}