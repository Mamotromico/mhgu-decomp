extern "C" int func_60524d40(const void *base, unsigned int bit)
{
    unsigned int word_index = bit >> 5;
    unsigned int bit_index = bit & 0x1f;
    const unsigned int *words = (const unsigned int *)((const char *)base + word_index * 4 + 0x358c);
    unsigned int v = *words;
    return (v & (1u << bit_index)) != 0 ? 1 : 0;
}