extern "C" int func_60524de0(int *base, unsigned int bit)
{
    unsigned int word = (unsigned int)bit >> 5;
    unsigned int off = bit & 0x1f;
    int v = base[word + 0x35ec / 4];
    int r = v & (1 << off);
    if (r != 0)
        return 1;
    return 0;
}