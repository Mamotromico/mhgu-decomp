extern "C" void func_6025f5e8(char *base, unsigned idx, unsigned mask)
{
    if (idx > 0x53)
        return;
    unsigned char v = *(unsigned char *)(base + idx + 0x1384e);
    char *p = base + v * 0x560;
    unsigned *q = (unsigned *)(p + 0x13c38);
    unsigned w = *q;
    w &= ~mask;
    *q = w;
}