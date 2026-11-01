extern "C" int func_605245d4(const unsigned char *base, unsigned int bit)
{
    const unsigned int *p = (const unsigned int *)(base + (bit >> 5) * 4);
    unsigned int v = (p[0xd70 / 4] >> (bit & 0x1f)) & 1;
    return v != 0;
}