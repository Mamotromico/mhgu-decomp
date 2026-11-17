extern "C" int strcmp(const char *, const char *);

extern "C" int func_6122ced4(const char **a, const char **b)
{
    const char *s0 = *(const char **)((const char *)b + 0x14);
    const char *s1 = *(const char **)((const char *)a + 0x14);
    if (s1 == s0)
        return 0;
    return (unsigned)strcmp(s1, s0) >> 31;
}