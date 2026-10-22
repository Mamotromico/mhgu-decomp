struct S {
    unsigned char pad0[0x4c];
    unsigned int field_4c;
    unsigned char pad1[0x54 - 0x50];
    unsigned int field_54;
};

extern "C" void func_605650e8(S *s, unsigned int value) {
    s->field_54 = value;
    s->field_4c |= 4u;
}