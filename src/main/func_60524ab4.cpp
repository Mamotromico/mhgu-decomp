extern "C" unsigned int func_60524ab4(unsigned char *base, unsigned int bit)
{
    unsigned int word = *(unsigned int *)(base + (bit >> 5) * 4 + 0x2a0c);
    return (word & (1u << (bit & 0x1f))) != 0 ? 1u : 0u;
}