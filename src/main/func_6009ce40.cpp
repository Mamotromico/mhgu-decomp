extern "C" void func_6009ce40(char *base, unsigned int mask)
{
    unsigned int *p = *(unsigned int **)(base + 0x1428);
    p[0x3a8 / 4] &= ~mask;
}