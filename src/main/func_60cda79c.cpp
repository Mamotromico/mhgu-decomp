struct S {
    unsigned char pad0[0x19];
    unsigned char field_19;
    unsigned char pad1[0x1c - 0x1a];
    unsigned int field_1c;
    unsigned int field_20;
};

extern "C" void func_60cda79c(S* p, unsigned int value_1c, unsigned int value_20, unsigned char value_19)
{
    p->field_1c = value_1c;
    p->field_20 = value_20;
    p->field_19 = value_19;
}