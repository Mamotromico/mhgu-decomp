struct S_600dcc3c {
    unsigned char pad_0[4];
    unsigned short field_4;
    unsigned char pad_6[0x1f];
    unsigned char field_25;
};

extern "C" unsigned char func_600dcc3c(const S_600dcc3c *s)
{
    unsigned char result = 0;
    if ((s->field_4 & 0x1f) == 0x14)
        result = s->field_25;
    return result;
}