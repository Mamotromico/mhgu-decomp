extern "C" void func_60644d20(char *p, int i)
{
    p += i * 8;
    *(int *)(p + 0x248) = -1;
    *(unsigned short *)(p + 0x24c) = 0xffff;
}