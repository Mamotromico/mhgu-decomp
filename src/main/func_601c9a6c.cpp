extern "C" void func_601c9a6c(char *p, unsigned v)
{
    if (*(unsigned *)(p + 0x6c) != 0)
        return;
    *(unsigned *)(p + 0x68) = 0;
    *(unsigned *)(p + 0x4) = 3;
    *(unsigned *)(p + 0x0) = v;
    *(unsigned *)(p + 0x6c) = 1;
}