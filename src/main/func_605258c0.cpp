extern "C" int func_605258c0(char *base, int bit)
{
    unsigned int *word = (unsigned int *)(base + ((unsigned int)bit >> 5) * 4 + 0x3648);
    unsigned int mask = 1u << (bit & 0x1f);
    return (*word & mask) ? 1 : 0;
}