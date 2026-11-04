extern "C" int func_6069d9e8(char *p, int a1, int a2)
{
    unsigned int count = *(unsigned int *)(p + 0x68);
    if (count == 0)
        return 0;
    char **arr = *(char ***)(p + 0x74);
    for (unsigned int i = 0; i < count; i++) {
        char *e = arr[i];
        if (e == 0)
            continue;
        signed char f4 = *(signed char *)(e + 4);
        if (f4 != a1)
            continue;
        signed char f5 = *(signed char *)(e + 5);
        if (f5 & a2)
            return (int)e;
    }
    return 0;
}