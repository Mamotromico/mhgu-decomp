extern "C" void func_6115f2b8(char *p)
{
    *(volatile unsigned char *)(*(unsigned int *)(p + 0x3328) + 0x642) = 0;
    char *q = *(char **)(p + 0x3ac4);
    if (*(unsigned int *)(q + 0xac) != 0)
        *(volatile unsigned char *)(q + 0x71) = 1;
}