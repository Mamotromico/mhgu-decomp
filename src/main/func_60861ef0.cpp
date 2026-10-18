struct func_60861ef0_s {
    unsigned char pad0[0x3c0];
    volatile unsigned char field_3c0;
    unsigned char pad1[0x67];
    volatile unsigned char field_428;
};

extern "C" void func_60861ef0(struct func_60861ef0_s *p, unsigned char v)
{
    p->field_3c0 = v;
    p->field_428 = v;
}