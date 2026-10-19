struct func_600dcc08_struct {
    unsigned char pad0[4];
    unsigned short field4;
    unsigned char pad6[0x1f - 6];
    unsigned char field1f;
};

extern "C" void func_600dcc08(func_600dcc08_struct* obj, unsigned char value) {
    if ((obj->field4 & 0x1f) == 0x14) {
        obj->field1f = value;
    }
}