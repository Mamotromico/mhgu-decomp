extern "C" int func_60524e30(const unsigned char *base, unsigned int bit)
{
    unsigned int word = *(const unsigned int *)(base + 0x3608 + (bit >> 5) * 4);
    unsigned int masked = word & (1u << (bit & 0x1f));
    return masked != 0;
}