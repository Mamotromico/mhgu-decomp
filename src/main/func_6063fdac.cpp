struct S_6063fdac {
    char pad0[0x4c];
    unsigned int field_4c;
    char pad50[0x0d];
    unsigned char field_5d;
};

extern "C" void func_6063fdac(S_6063fdac *p, unsigned char v)
{
    p->field_4c |= 0x20;
    p->field_5d = v;
}