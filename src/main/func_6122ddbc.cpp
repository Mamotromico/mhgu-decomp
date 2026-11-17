extern "C" char *strncpy(char *dst, const char *src, unsigned n);

extern "C" char *func_6122ddbc(char *dst, const char *src, unsigned n)
{
    char *tmp = dst;
    dst = (char *)src;
    src = tmp;
    return strncpy(dst, src, n);
}