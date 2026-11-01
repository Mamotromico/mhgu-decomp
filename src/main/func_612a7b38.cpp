extern "C" void func_612a7b38(unsigned char *dst, const unsigned char *src)
{
    dst[0x04] = src[0x04];
    *(unsigned int *)(dst + 0x08) = *(const unsigned int *)(src + 0x08);
    unsigned int a = *(const unsigned int *)(src + 0x10);
    unsigned int b = *(const unsigned int *)(src + 0x14);
    *(unsigned int *)(dst + 0x14) = b;
    *(unsigned int *)(dst + 0x10) = a;
    *(unsigned int *)(dst + 0x18) = *(const unsigned int *)(src + 0x18);
}