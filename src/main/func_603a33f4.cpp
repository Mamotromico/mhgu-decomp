struct func_603a33f4_inner {
    unsigned char pad_0x00[0x56];
    unsigned char field_0x56;
};

struct func_603a33f4_outer {
    unsigned char pad_0x00[0xa4];
    func_603a33f4_inner *field_0xa4;
};

extern "C" int func_603a33f4(func_603a33f4_outer *self)
{
    func_603a33f4_inner *p = self->field_0xa4;
    unsigned char v = 0;
    if (p != 0)
        v = p->field_0x56;
    return (int)(signed char)v;
}