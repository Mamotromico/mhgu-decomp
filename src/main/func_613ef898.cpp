extern "C" void *func_613ef898(unsigned char *p, unsigned a, unsigned b)
{
    unsigned cnt = *(unsigned *)(p + 0x8);
    unsigned char *ret = 0;
    if ((int)cnt > 4)
        return 0;
    unsigned off = *(unsigned *)(p + 0xc);
    unsigned cap = *(unsigned *)(p + 0x4);
    unsigned newoff = b * a + off;
    if (cap < newoff)
        return 0;
    unsigned char *base = *(unsigned char **)(p + 0x0);
    *(unsigned *)(p + 0x8) = cnt + 1;
    *(unsigned *)(p + 0xc) = newoff;
    ret = base + off;
    return ret;
}