extern "C" unsigned int func_6016b920(char *base)
{
    unsigned short *p = (unsigned short *)(base + 0x202c);
    unsigned int v = (unsigned int)*p + 1u;
    unsigned int u = v & 0xffffu;
    if (u > 0xea5fu)
        v = 0;
    *p = (unsigned short)v;
    return v & 0xffffu;
}