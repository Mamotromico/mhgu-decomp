extern "C" int func_60523984(const char *a, unsigned int bit)
{
    const unsigned int *p = (const unsigned int *)(a + ((bit >> 5) << 2));
    unsigned int word = *(const unsigned int *)((const char *)p + 0x35e4);
    unsigned int mask = 1u << (bit & 0x1f);
    if ((word & mask) != 0)
        return 1;
    return 0;
}