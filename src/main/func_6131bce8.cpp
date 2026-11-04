extern "C" void func_6131bce8(void *r0, void *r1)
{
    unsigned char *d = (unsigned char *)r0;
    unsigned char *s = (unsigned char *)r1;
    unsigned int r;

    r = *(unsigned int *)(s + 0x0);
    *(unsigned int *)(d + 0x14) = r;
    d[0x2c] = 1;
    r = *(unsigned int *)(s + 0x4);
    *(unsigned int *)(d + 0x18) = r;
    d[0x2d] = 1;
    r = *(unsigned int *)(s + 0x8);
    *(unsigned int *)(d + 0x1c) = r;
    d[0x2e] = 1;
    r = *(unsigned int *)(s + 0xc);
    *(unsigned int *)(d + 0x20) = r;
    d[0x2f] = 1;
    r = *(unsigned int *)(s + 0x10);
    *(unsigned int *)(d + 0x24) = r;
    d[0x30] = 1;
    r = *(unsigned int *)(s + 0x14);
    *(unsigned int *)(d + 0x28) = r;
    d[0x31] = 1;
    r = *(unsigned int *)(d + 0x5e0);
    r |= 1;
    *(unsigned int *)(d + 0x5e0) = r;
}