struct Data600dafb4 {
    char pad_0[4];
    unsigned short field_4;
    char pad_6[10];
    unsigned int field_10;
};

extern "C" void func_600dafb4(Data600dafb4 *p, unsigned int mask)
{
    unsigned int v = p->field_4 & 0x1f;
    if (v == 0xd || v == 0xb) {
        p->field_10 = p->field_10 & ~mask;
    }
}