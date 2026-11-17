extern "C" void func_60c1b778(void *dst, const void *src);

static void copy(void *d, const void *s)
{
    *(unsigned *)((char *)d + 0x04) = *(const unsigned *)((const char *)s + 0x04);
    *(unsigned *)((char *)d + 0x08) = *(const unsigned *)((const char *)s + 0x08);
    *(unsigned *)((char *)d + 0x0c) = *(const unsigned *)((const char *)s + 0x0c);
    *(unsigned *)((char *)d + 0x10) = *(const unsigned *)((const char *)s + 0x10);
    *(unsigned *)((char *)d + 0x14) = *(const unsigned *)((const char *)s + 0x14);
    *(unsigned *)((char *)d + 0x18) = *(const unsigned *)((const char *)s + 0x18);
    *(unsigned *)((char *)d + 0x1c) = *(const unsigned *)((const char *)s + 0x1c);
    *(unsigned *)((char *)d + 0x20) = *(const unsigned *)((const char *)s + 0x20);
    *(unsigned *)((char *)d + 0x24) = *(const unsigned *)((const char *)s + 0x24);
    *(unsigned *)((char *)d + 0x28) = *(const unsigned *)((const char *)s + 0x28);
    *(unsigned *)((char *)d + 0x2c) = *(const unsigned *)((const char *)s + 0x2c);
    *(unsigned short *)((char *)d + 0x30) = *(const unsigned short *)((const char *)s + 0x30);
    *(unsigned char *)((char *)d + 0x32) = *(const unsigned char *)((const char *)s + 0x32);
}

extern "C" void func_60c1b778(void *dst, const void *src)
{
    copy(dst, src);
}