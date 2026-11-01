extern "C" int func_605245f8(void *p, unsigned int bit)
{
    if (bit > 0x5f)
        return 0;
    unsigned int word = bit >> 5;
    unsigned int off = bit & 0x1f;
    unsigned char *base = (unsigned char *)p;
    unsigned int val = *(unsigned int *)(base + 0xd78 + word * 4);
    return (val & (1u << off)) != 0;
}