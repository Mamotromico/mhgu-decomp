struct S {
    unsigned char pad0[0x5c];
    unsigned int field_5c;
    unsigned char pad_60[0x8];
    unsigned int field_68;
};

extern "C" void func_605f3d10(S* s, unsigned int value) {
    s->field_5c = value;
    s->field_68 |= 1u;
}