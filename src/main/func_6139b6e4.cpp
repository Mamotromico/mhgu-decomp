struct S_6139b6e4 {
    unsigned char pad_00[0x40];
    volatile int field_40;
    volatile int field_44;
    unsigned char pad_48[0x04];
    volatile int field_4c;
    unsigned char pad_50[0x0c];
    volatile unsigned char field_5c;
};

extern "C" void func_6139b6e4(S_6139b6e4 *p) {
    p->field_4c = 0;
    p->field_5c = 0;
    p->field_44 = 0;
    p->field_40 = 0;
}