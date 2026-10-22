struct func_605fe194_struct {
    unsigned char pad[0x50];
    unsigned int field_50;
    unsigned int field_54;
};

extern "C" void func_605fe194(func_605fe194_struct *p, unsigned int value)
{
    p->field_50 = value;
    p->field_54 |= 2;
}