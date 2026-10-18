struct func_60a49bac_obj {
    unsigned char pad0[0x90];
    unsigned int a;
    unsigned char pad1[4];
    unsigned int b;
};

extern "C" void func_60a49bac(volatile struct func_60a49bac_obj *p, unsigned int x, unsigned int y)
{
    p->a = x;
    p->b = y;
}