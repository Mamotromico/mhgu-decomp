extern "C" int func_60285e78(const unsigned char *base, unsigned int idx)
{
    unsigned int word = idx >> 5;
    unsigned int bit = idx & 0x1f;
    const unsigned int *p = (const unsigned int *)(base + word * 4);
    unsigned int v = *(const unsigned int *)((const unsigned char *)p + 0x1424);
    unsigned int mask = 1u << bit;
    unsigned int r = v & mask;
    return r ? 1 : 0;
}