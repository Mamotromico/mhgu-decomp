extern "C" int func_600daffc(const unsigned char *p, unsigned int mask)
{
    unsigned int f = *(const unsigned short *)(p + 4);
    unsigned int t = f & 0x1f;
    int r;
    if (t == 0xd || t == 0xb)
        r = (*(const unsigned int *)(p + 0x10) & mask) != 0;
    else
        r = 0;
    return r;
}