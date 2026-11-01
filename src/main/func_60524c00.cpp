extern "C" int func_60524c00(void *base, int bit)
{
    unsigned int idx = (unsigned int)bit >> 5;
    unsigned int off = (unsigned int)bit & 0x1f;
    unsigned int val = *(unsigned int *)((char *)base + idx * 4 + 0x3490);
    return (int)((val & (1u << off)) != 0);
}