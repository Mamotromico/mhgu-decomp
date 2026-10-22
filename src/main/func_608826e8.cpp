struct Data608826e8 {
    unsigned char pad_000[0x184];
    unsigned char field_184;
    unsigned char pad_185[0x18];
    unsigned char field_19d;
};

extern "C" unsigned int func_608826e8(Data608826e8 *p)
{
    p->field_184 = 0;
    return (p->field_19d >> 3) & 1;
}