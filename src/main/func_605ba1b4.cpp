extern "C" unsigned int func_605ba1b4(unsigned char *p, unsigned short v, unsigned int flags)
{
    if ((flags & 1) && *(unsigned short *)(p + 0x50) == v)
        return (unsigned int)p;
    *(unsigned short *)(p + 0x50) = v;
    *(unsigned char *)(p + 0x53) = (flags >> 1) & 1;
    *(unsigned char *)(p + 0x52) = 1;
    return (unsigned int)p;
}