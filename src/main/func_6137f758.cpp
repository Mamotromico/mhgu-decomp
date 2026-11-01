extern "C" int func_6137f758(char *p)
{
    if (*(unsigned int *)(p + 0xbc) != 5)
        return 0;
    unsigned int v = *(unsigned int *)(p + 0xa8);
    unsigned int r = v - 2;
    return r < 3 ? 1 : 0;
}