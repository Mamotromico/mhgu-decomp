struct S {
    unsigned char pad_0[0x10];
    unsigned int field_10;
    unsigned char pad_14[0xcd8 - 0x14];
    unsigned int field_cd8;
};

extern "C" void func_6131a108(S *p, unsigned int v) {
    p->field_10 = v;
    p->field_cd8 |= 0x10u;
}