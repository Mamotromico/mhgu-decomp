extern "C" unsigned short func_600e0e54(void *self, unsigned int index)
{
    unsigned int r0 = 0;
    if (index > 0x13)
        return (unsigned short)r0;
    unsigned char *base = (unsigned char *)self;
    unsigned int ptr = *(unsigned int *)(base + 0x188);
    if (ptr == 0)
        return (unsigned short)r0;
    unsigned char *p = (unsigned char *)(ptr + index * 2);
    return *(unsigned short *)(p + 0x3a0);
}