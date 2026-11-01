extern "C" void func_6005bea8(void *base)
{
    volatile unsigned char *p = (volatile unsigned char *)base;
    p[0x2a0c] = 0xff;
    *(volatile unsigned int *)(p + 0x2a08) = 0xbf800000u;
}