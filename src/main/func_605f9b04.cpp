struct S {
    unsigned char pad0[0x4c];
    unsigned int field_4c;
    unsigned int field_50;
};

extern "C" void func_605f9b04(S* s, unsigned int value) {
    unsigned int v = s->field_50;
    s->field_4c = value;
    s->field_50 = v | 1;
}