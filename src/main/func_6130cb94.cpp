extern "C" int func_6130cb94(const unsigned char *p)
{
    unsigned int v = *(const unsigned int *)p;
    unsigned int hi = v >> 24;
    unsigned int mid = v >> 16;
    if (hi == 0xa)
        return 1;
    if (hi == 0xac && (mid & 0xf0) == 0x10)
        return 1;
    if (hi == 0xc0) {
        mid &= 0xff;
        if (mid == 0xa8)
            return 1;
        return 0;
    }
    return 0;
}