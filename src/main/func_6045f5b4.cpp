extern "C" int func_6045f5b4(char *s, unsigned v)
{
    unsigned n = *(unsigned char *)(s + 0x15eb);
    if (n == 0)
        return 0;
    unsigned *p = (unsigned *)(s + 0x15c8);
    for (unsigned i = 0; i < n; i++) {
        if (p[i] == v)
            return 1;
    }
    return 0;
}