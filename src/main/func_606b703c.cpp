struct S606b703c {
    unsigned char pad0[0x7d];
    unsigned char field_7d;
    unsigned char pad1[0x2];
    unsigned short field_80;
};

extern "C" void func_606b703c(S606b703c *p)
{
    p->field_80 = 0;
    p->field_7d = 0;
}