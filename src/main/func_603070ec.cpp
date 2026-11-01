struct S {
    unsigned char pad[0x13b0];
    volatile unsigned int field_13b0;
    volatile unsigned int field_13b4;
    volatile unsigned int field_13b8;
};

extern "C" void func_603070ec(S* p) {
    p->field_13b4 = 0;
    p->field_13b0 = 0;
    p->field_13b8 = 0;
}