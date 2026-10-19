struct S_600dcdd8 {
    unsigned char pad0[4];
    unsigned short field_4;
    unsigned char pad6[0x1d - 6];
    unsigned char field_1d;
};

extern "C" void func_600dcdd8(S_600dcdd8 *s, unsigned char value)
{
    if ((s->field_4 & 0x1f) == 0x14)
        s->field_1d = value;
}