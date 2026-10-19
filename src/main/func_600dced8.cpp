struct func_600dced8_S {
    char pad0[4];
    unsigned short field4;
    char pad6[0x15];
    unsigned char field1b;
};

extern "C" void func_600dced8(func_600dced8_S* p, unsigned char value) {
    if ((p->field4 & 0x1f) == 0x14) {
        p->field1b = value;
    }
}