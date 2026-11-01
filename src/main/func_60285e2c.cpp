extern "C" int func_60285e2c(unsigned char *p, unsigned int bit)
{
    unsigned int word = (bit >> 5) * 4;
    unsigned int bits = *(unsigned int *)(p + 0x1414 + word);
    unsigned int mask = 1u << (bit & 0x1f);
    return (bits & mask) != 0;
}