extern "C" int func_60194c50(const unsigned char *base, const unsigned char *hdr)
{
    if (hdr == 0)
        return 0;
    unsigned int v = *(const unsigned short *)(hdr + 4);
    unsigned char b = base[(v >> 3) + 0x50];
    unsigned int bit = v & 7;
    unsigned int m = b & (1u << bit);
    return m != 0 ? 1 : 0;
}