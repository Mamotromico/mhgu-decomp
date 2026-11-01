extern "C" int func_601a6490(const unsigned char *base, unsigned int bit)
{
    unsigned int word = *(const unsigned int *)(base + ((bit >> 5) * 4) + 0x108);
    unsigned int mask = 1u << (bit & 0x1f);
    return (word & mask) != 0;
}