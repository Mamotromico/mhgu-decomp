struct S {
    unsigned char pad_0[0x54];
    unsigned int field_54;
    unsigned char pad_58[0x0c];
    unsigned int field_64;
};

extern "C" void func_605f5354(S* s, unsigned int value) {
    s->field_64 = value;
    s->field_54 |= 0xff;
}