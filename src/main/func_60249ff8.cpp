extern "C" void func_60249ff8(unsigned char *base, unsigned char v)
{
    base += 0x137b;
    unsigned char t = *base;
    base[0x1] = t;
    base[0x0] = v;
    *(unsigned int *)(base - 0x1377) = 0;
    *(unsigned int *)(base + 0x5) = 0;
}