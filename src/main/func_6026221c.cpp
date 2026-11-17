extern "C" unsigned char *func_6026221c(unsigned char *p, unsigned int n)
{
    unsigned char v = *(unsigned char *)(p += 0x48ab8);
    unsigned char *q = p + n * 0x560;
    return (v > n) ? q + 8 : 0;
}