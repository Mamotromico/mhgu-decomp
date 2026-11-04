extern "C" void func_612fbad4(unsigned char *dst, const unsigned char *src)
{
    dst[0x4] = src[0x4];
    dst[0x5] = src[0x5];
    dst[0x6] = src[0x6];
    dst[0x7] = src[0x7];
    unsigned int a = *(const unsigned int *)(src + 0x8);
    unsigned int b = *(const unsigned int *)(src + 0xc);
    *(unsigned int *)(dst + 0xc) = b;
    *(unsigned int *)(dst + 0x8) = a;
    *(unsigned int *)(dst + 0x10) = *(const unsigned int *)(src + 0x10);
    *(unsigned int *)(dst + 0x14) = *(const unsigned int *)(src + 0x14);
    dst[0x18] = src[0x18];
    *(unsigned short *)(dst + 0x1a) = *(const unsigned short *)(src + 0x1a);
}