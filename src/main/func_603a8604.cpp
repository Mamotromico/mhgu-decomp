extern "C" int func_603a8604(char *base, unsigned int mask)
{
    int r = -1;
    if ((*(unsigned int *)(base + 0xec) & mask) == mask)
        r = 0;
    else if ((*(unsigned int *)(base + 0xf8) & mask) == mask)
        r = 1;
    else if ((*(unsigned int *)(base + 0x104) & mask) == mask)
        r = 2;
    return r;
}