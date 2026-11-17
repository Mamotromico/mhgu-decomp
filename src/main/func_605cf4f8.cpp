extern "C" void func_605cf4f8(char *p, int flag)
{
    unsigned int v = *(unsigned int *)(p + 0x5c);
    if (flag != 0)
        v |= 1u;
    else
        v &= ~1u;
    *(unsigned int *)(p + 0x5c) = v;
}