struct S_600dcd38 {
    unsigned char pad_0[4];
    unsigned short field_4;
    unsigned char pad_6[0x16];
    unsigned char field_1c;
};

extern "C" void func_600dcd38(S_600dcd38 *p, unsigned char value) {
    if ((p->field_4 & 0x1f) == 0x14) {
        p->field_1c = value;
    }
}