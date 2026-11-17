extern "C" char *func_6019b360(char *dst, unsigned idx, const char *src)
{
    if (idx > 0x17)
        return dst;
    return __builtin_strcpy(dst + idx * 0xaa + 0x62f4, src);
}