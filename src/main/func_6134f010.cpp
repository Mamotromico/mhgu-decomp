extern "C" int func_6134f010(const char *p, unsigned int i)
{
    if (i > 5)
        return 0;
    unsigned int v = *(const unsigned int *)(p + 0x6ec);
    unsigned int m = 1u << (i + 3);
    return (v & m) != 0;
}