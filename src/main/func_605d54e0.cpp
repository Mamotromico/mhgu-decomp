extern "C" int func_60545c20(unsigned, unsigned);

extern "C" int func_605d54e0(void *p)
{
    unsigned a = *(unsigned *)((char *)p + 0x24);
    unsigned b = *(unsigned *)((char *)p + 0x28);
    return func_60545c20(a, b);
}