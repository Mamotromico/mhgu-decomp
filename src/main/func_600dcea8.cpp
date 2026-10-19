struct S600dcea8 {
    unsigned char pad0[4];
    unsigned short field4;
    unsigned char pad6[0x14];
    unsigned char field1a;
};

extern "C" void func_600dcea8(S600dcea8* p, unsigned char v) {
    if ((p->field4 & 0x1f) == 0x14) {
        p->field1a = v;
    }
}