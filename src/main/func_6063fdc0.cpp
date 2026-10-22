struct S_6063fdc0 {
    char pad_0[0x4c];
    unsigned int field_4c;
    char pad_50[0x0e];
    unsigned char field_5e;
};

extern "C" void func_6063fdc0(S_6063fdc0 *s, unsigned char value) {
    s->field_4c |= 0x80u;
    s->field_5e = value;
}