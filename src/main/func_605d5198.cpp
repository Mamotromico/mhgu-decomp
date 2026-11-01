extern "C" int func_605d5198(void *p)
{
    char *b = (char *)p;
    if (*(int *)(b + 0x50) == 3)
        return 1;
    return *(int *)(b + 0x54) == 1;
}