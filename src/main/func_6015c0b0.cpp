struct S_6015c0b0 {
    unsigned char pad0[0x28];
    unsigned short field_28;
    unsigned char pad_2a[0x2c - 0x2a];
    unsigned char field_2c;
    unsigned char pad_2d[0x2e - 0x2d];
    unsigned char field_2e;
    unsigned char pad_2f[0x31 - 0x2f];
    unsigned char field_31;
};

extern "C" void func_6015c0b0(S_6015c0b0 *p) {
    p->field_2c = 0;
    p->field_2e = 1;
    p->field_28 = 0;
    p->field_31 = 3;
}