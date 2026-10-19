extern "C" char *func_6019a4dc(char *base, int offset, char value)
{
    char *p = base + offset;
    *(volatile char *)(p + 0x59f2) = value;
    return p;
}