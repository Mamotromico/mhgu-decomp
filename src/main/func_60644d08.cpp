extern "C" int func_60644d08(char *base, unsigned int index, int value32, short value16)
{
    base += index * 8;
    *(int *)(base + 0x248) = value32;
    *(short *)(base + 0x24c) = value16;
    return 1;
}