extern "C" int func_600e9ee8(unsigned char *p, unsigned char c)
{
    unsigned char *q = p + 0x254;
    unsigned i;
    for (i = 0; i < 0x10; i++) {
        if (q[i] == c)
            return 1;
    }
    return 0;
}