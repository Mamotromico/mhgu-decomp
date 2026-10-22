struct S_60575954 {
    unsigned char pad0[0x6c];
    unsigned char field_6c;
    unsigned char pad1[0x7];
    unsigned int field_74;
};

extern "C" void func_60575954(S_60575954 *p, unsigned char value)
{
    p->field_6c = value;
    p->field_74 |= 8u;
}