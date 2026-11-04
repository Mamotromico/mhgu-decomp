extern "C" int func_6005d448(void *base)
{
    unsigned char *p = (unsigned char *)base;
    if (*(int *)(p + 0x1c) == 0)
        return 0;
    if (*(int *)(p + 0x20) == 0)
        return 1;
    if (*(int *)(p + 0x24) == 0)
        return 2;
    if (*(int *)(p + 0x28) == 0)
        return 3;
    if (*(int *)(p + 0x2c) == 0)
        return 4;
    if (*(int *)(p + 0x30) == 0)
        return 5;
    if (*(int *)(p + 0x34) == 0)
        return 6;
    if (*(int *)(p + 0x38) == 0)
        return 7;
    if (*(int *)(p + 0x3c) == 0)
        return 8;
    if (*(int *)(p + 0x40) == 0)
        return 9;
    return -1;
}