extern "C" int func_60277224(char *base, int index) {
    int *entry = (int *)(base + (index << 2));
    char *p = *(char **)((char *)entry + 0x1c);
    if (p == 0)
        return 0;
    if (*(int *)(p + 0x13c8) != 0)
        return 0;
    return (int)p;
}