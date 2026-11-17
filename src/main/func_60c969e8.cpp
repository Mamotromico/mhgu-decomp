extern "C" void func_60c969e8(void *dst, const void *src, unsigned n)
{
    unsigned char *d = (unsigned char *)dst + 4;
    const unsigned char *s = (const unsigned char *)src + 4;
    if (n != 0)
        n -= 4;
    __builtin_memcpy(d, s, n);
}