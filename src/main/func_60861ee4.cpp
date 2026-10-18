struct func_60861ee4_s {
    unsigned char pad1[0x3b0];
    unsigned int field_3b0;
    unsigned char pad2[0x6c];
    unsigned int field_420;
};

extern "C" void func_60861ee4(func_60861ee4_s *p, unsigned int v)
{
    p->field_3b0 = v;
    p->field_420 = v;
}