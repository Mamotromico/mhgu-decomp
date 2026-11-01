extern "C" void func_606a9538(char *base)
{
    unsigned char *p = (unsigned char *)base;
    if (p[0x44] != 0)
        return;
    p[0x44] = 1;
    *(unsigned int *)(p + 0x38) = 0x11;
    *(unsigned int *)(p + 0x3c) = 0x5a;
}