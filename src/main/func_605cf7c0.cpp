extern "C" void func_605cf7c0(char *base, unsigned val)
{
    *(unsigned *)(base + 0x6c) = val;
    unsigned v = *(unsigned *)(base + 0x5c);
    unsigned r = v & ~2u;
    if (val != 0)
        r = v | 2u;
    *(unsigned *)(base + 0x5c) = r;
}