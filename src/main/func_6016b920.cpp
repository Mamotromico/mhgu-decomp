extern "C" unsigned int func_6016b920(char *base)
{
    unsigned short *p = (unsigned short *)(base + 0x202c);
    unsigned short v = *p;
    v++;
    if (v > 0xea5fu)
        v = 0;
    *p = v;
    return v;
}
