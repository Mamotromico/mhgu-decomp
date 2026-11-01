extern "C" int func_603a8b7c(const unsigned char *p)
{
    unsigned int v = *(const volatile unsigned int *)(p + 0xec);
    if (!(v & 0x80000))
    {
        v = *(const volatile unsigned int *)(p + 0xf8);
        if (!(v & 0x80000))
        {
            v = *(const volatile unsigned int *)(p + 0x104);
            if (!(v & 0x80000))
                return 0;
        }
    }
    return (v & 0x60) == 0x20 ? 1 : 0;
}