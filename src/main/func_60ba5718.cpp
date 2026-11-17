extern "C" void func_60ba5718(char *p, unsigned char b)
{
    *(unsigned char *)(p + 0x40) = b;

    unsigned long long v = *(unsigned long long *)(p + 0x48);

    *(unsigned int *)(p + 0x54) = (unsigned int)(v >> 32);
    *(unsigned int *)(p + 0x50) = (unsigned int)v;

    *(unsigned int *)(p + 0x5c) = 0;
    *(unsigned int *)(p + 0x58) = 0;
    *(unsigned int *)(p + 0x68) = 0x3f800000u;
    *(unsigned int *)(p + 0x78) = 0;
}