struct Data_600dcb8c {
    unsigned char pad0[4];
    unsigned short field4;
    unsigned char pad6[0x10 - 6];
    unsigned char field10;
};

extern "C" unsigned int func_600dcb8c(const Data_600dcb8c *p)
{
    return ((p->field4 & 0x1f) == 0x14) ? p->field10 : 0;
}