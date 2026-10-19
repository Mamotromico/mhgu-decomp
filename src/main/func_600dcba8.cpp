struct func_600dcba8_struct {
    unsigned char pad0[4];
    unsigned short field_4;
    unsigned char pad1[0xA];
    unsigned char field_10;
};

extern "C" void func_600dcba8(func_600dcba8_struct* s, unsigned char v)
{
    if ((s->field_4 & 0x1f) == 0x14) {
        s->field_10 = v;
    }
}