extern "C" int func_600daeb8(const unsigned char *p)
{
    unsigned x = *(const unsigned short *)(p + 4) & 0x1f;
    unsigned t = x - 0x17;
    unsigned u = x - 1;
    int r1 = (t < 2) ? 1 : 0;
    int r2 = (u < 5) ? 1 : 0;
    return r2 | r1;
}