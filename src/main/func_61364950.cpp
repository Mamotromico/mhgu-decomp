extern "C" int func_61354214(int);

extern "C" int func_61364950(char *p)
{
    int r = func_61354214(*(int *)(p + 0x44));
    if (r != 1)
        r = 0;
    *(char *)(p + 0x58) = (char)r;
    return 1;
}