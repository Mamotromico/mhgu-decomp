extern "C" int func_60524cf0(const unsigned char *base, unsigned int bit)
{
    unsigned int word = *(const unsigned int *)(base + 0x3570 + ((bit >> 5) * 4));
    return (word & (1u << (bit & 0x1f))) ? 1 : 0;
}