struct struct_6130e468 {
    char pad0[0x10];
    unsigned int field10;
    unsigned char field14;
    char pad15[0x5c3];
    unsigned int field5d8;
};

extern "C" void func_6130e468(struct_6130e468 *p, unsigned int a, unsigned char b)
{
    p->field10 = a;
    p->field14 = b;
    p->field5d8 |= 2u;
}