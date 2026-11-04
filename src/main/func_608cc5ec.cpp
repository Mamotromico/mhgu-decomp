extern "C" int func_608cc5ec(const unsigned char *p)
{
    if (*(const unsigned int *)(p + 0x0) == 0)
        return 0;
    if (!(*(const unsigned int *)(p + 0x10) != 0 && *(const unsigned int *)(p + 0x4) != 0))
        return 0;
    if (!(*(const unsigned int *)(p + 0x14) != 0 && *(const unsigned int *)(p + 0x8) != 0))
        return 0;
    if (!(*(const unsigned int *)(p + 0x18) != 0 && *(const unsigned int *)(p + 0xc) != 0))
        return 0;
    if (*(const unsigned int *)(p + 0x1c) != 0)
        return 1;
    return 0;
}