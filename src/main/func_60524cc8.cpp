extern "C" int func_60524cc8(unsigned char *base, unsigned int bit)
{
    unsigned int word = bit >> 5;
    unsigned int shift = bit & 0x1f;
    unsigned int *p = (unsigned int *)(base + word * 4);
    unsigned int val = *(unsigned int *)((unsigned char *)p + 0x3548);
    unsigned int masked = val & (1u << shift);
    return masked != 0;
}