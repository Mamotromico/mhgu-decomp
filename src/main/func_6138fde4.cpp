extern "C" int func_6130cdcc(unsigned);

extern "C" int func_6138fde4(unsigned char *p)
{
    unsigned v = *(unsigned *)(p + 0x20);
    if (v == 0)
        return 0;
    return func_6130cdcc(v);
}