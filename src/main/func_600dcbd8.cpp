struct Data_600dcbd8 {
    char pad0[4];
    unsigned short field4;
    char pad6[0x11 - 6];
    unsigned char field17;
};

extern "C" void func_600dcbd8(Data_600dcbd8* p, unsigned char value)
{
    if ((p->field4 & 0x1f) == 0x14)
        p->field17 = value;
}