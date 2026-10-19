struct data_600dcd08 {
    unsigned int field_0;
    unsigned short field_4;
    unsigned char pad_6[0x0C];
    unsigned char field_12;
};

extern "C" void func_600dcd08(data_600dcd08 *p, unsigned char value)
{
    if ((p->field_4 & 0x1F) == 0x14)
        p->field_12 = value;
}