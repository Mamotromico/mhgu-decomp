extern "C" void func_60c71bb8(char *dst, const unsigned *src, unsigned char b)
{
    dst[0xf1] = 1;
    dst[0xfe] = 1;
    unsigned *d = (unsigned *)(dst + 0xb0);
    for (int i = 0; i < 16; ++i)
        d[i] = src[i];
    dst[0xf0] = (char)b;
}