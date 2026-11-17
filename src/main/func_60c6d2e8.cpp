extern "C" void func_60c6d2e8(char *dst, const char *src)
{
    for (int i = 0; i < 8; i++)
        ((unsigned *)(dst + 0xe0))[i] = ((const unsigned *)src)[i];
}