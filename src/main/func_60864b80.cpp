struct S {
    char pad0[0x14];
    unsigned int field_0x14;
    char pad1[0x4];
    unsigned int field_0x1c;
    unsigned int field_0x20;
};

extern "C" void func_60864b80(S* s, unsigned int a, unsigned int b) {
    s->field_0x14 = 1;
    s->field_0x1c = a;
    s->field_0x20 = b;
}