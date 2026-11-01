extern "C" int func_60525898(const unsigned int *base, unsigned int bit)
{
    unsigned int word = *(const unsigned int *)((const char *)base + (bit >> 5) * 4 + 0x3638);
    return (word & (1u << (bit & 0x1f))) ? 1 : 0;
}