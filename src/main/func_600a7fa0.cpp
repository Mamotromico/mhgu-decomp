extern "C" void func_600a7fa0(char *base)
{
    char *p = base;
    if (*(unsigned char *)(p + 0x73e4) != 0)
        return;
    if (*(unsigned char *)(p + 0x73e5) != 0)
        return;
    {
        char *q = *(char **)(p + 0x1428);
        unsigned char v = *(unsigned char *)(q + 0x5d2c);
        if (v != 0) {
            --v;
            *(unsigned char *)(q + 0x5d2c) = v;
        }
    }
}