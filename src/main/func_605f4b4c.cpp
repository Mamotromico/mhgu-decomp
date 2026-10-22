struct S {
    unsigned char pad0[0x4c];
    int field_4c;
    unsigned char pad1[0x1c];
    unsigned int field_6c;
};

extern "C" void func_605f4b4c(S *s, int v) {
    s->field_4c = v;
    s->field_6c |= 1u;
}