struct S_6000fb28 {
    unsigned char pad0[0xc4];
    volatile unsigned int field_c4;
    volatile unsigned char field_c8;
    volatile unsigned char field_c9;
    unsigned char pad_ca[2];
    volatile unsigned int field_cc;
};

extern "C" void func_6000fb28(S_6000fb28 *p) {
    p->field_c4 = 0;
    p->field_c8 = 0xff;
    p->field_c9 = 0xff;
    p->field_cc = 0xff;
}