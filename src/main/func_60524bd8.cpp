extern "C" int func_60524bd8(const char *base, unsigned int bit)
{
    unsigned int word = bit >> 5;
    unsigned int bitpos = bit & 0x1f;
    unsigned int val = *(const unsigned int *)(base + word * 4 + 0x3488);
    return (val & (1u << bitpos)) != 0;
}