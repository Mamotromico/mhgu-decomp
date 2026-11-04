extern "C" int func_60524a70(char *base, int idx, unsigned int bit)
{
    int tmp;
    if ((unsigned)(idx - 1) > 4)
        return 0;
    tmp = *(int *)(base + (idx - 1) * 0x360 + (bit >> 5) * 4 + 0x1908);
    tmp = tmp & (1 << (bit & 0x1f));
    return tmp != 0 ? 1 : 0;
}