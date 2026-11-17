extern "C" unsigned int func_6131c00c(const unsigned char *p)
{
    unsigned int a = *(const unsigned int *)(p + 0x4);
    unsigned int b = *(const unsigned int *)(p + 0x5e0);
    return ((a << 1) & 4u) | b;
}