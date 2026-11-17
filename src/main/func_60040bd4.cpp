extern "C" void func_60040bd4(unsigned char *dst, unsigned char *src)
{
    if (src == 0)
        return;
    *(unsigned *)(dst + 0x4) = src[0xf];
    dst[0x8] = src[0x11];
    dst[0x9] = src[0x12];
}