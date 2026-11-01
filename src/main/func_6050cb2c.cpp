struct S {
    unsigned char pad0[0x1e8];
    volatile unsigned int field_1e8;
    volatile unsigned char field_1ec;
    volatile unsigned char field_1ed;
    unsigned char pad_1ee[2];
    volatile unsigned int field_1f0;
};

extern "C" void func_6050cb2c(S *p) {
    p->field_1e8 = 0;
    p->field_1ed = 0xff;
    p->field_1ec = 0xff;
    p->field_1f0 = 0xff;
}