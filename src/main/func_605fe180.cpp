struct S {
    unsigned char pad0[0x4c];
    unsigned int field_4c;
    unsigned char pad1[0x4];
    unsigned int field_54;
};

extern "C" void func_605fe180(S* s, unsigned int v) {
    s->field_4c = v;
    s->field_54 |= 1u;
}