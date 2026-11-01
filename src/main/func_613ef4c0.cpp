extern "C" void func_613ef4c0(void **pp, unsigned char *out)
{
    if (out == 0)
        return;
    unsigned int *p = (unsigned int *)*pp;
    unsigned int v = p[1];
    v = __builtin_bswap32(v);
    *(unsigned int *)out = v;
    unsigned short h = *(unsigned short *)((char *)p + 2);
    h = __builtin_bswap16(h);
    *(unsigned short *)(out + 4) = h;
}