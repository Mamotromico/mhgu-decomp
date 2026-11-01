extern "C" int func_605258e8(const unsigned char *base, unsigned int bit)
{
    unsigned int word = *(const unsigned int *)(base + ((bit >> 5) * 4) + 0x3650);
    return (word & (1u << (bit & 0x1f))) != 0;
}