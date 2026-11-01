extern "C" int func_60b1f6d0(char *p, unsigned index) {
    if (*(unsigned *)(p + 0x10) <= index)
        return 0;
    char *arr = *(char **)(p + 0x1c);
    char *e = *(char **)(arr + index * 4);
    if (e == 0)
        return 0;
    return *(int *)(e + 0x54);
}