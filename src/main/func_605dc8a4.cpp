extern "C" int func_605dc8a4(const unsigned char *p)
{
    unsigned char b = p[0xf1];
    if (b != 1) {
        if (b == 0)
            return p[0xa4];
        return -1;
    }
    unsigned char a = p[0xa4];
    return a == 0 ? 2 : 3;
}