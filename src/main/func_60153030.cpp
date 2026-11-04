extern "C" int func_60153030(char *p) {
    unsigned int n = *(unsigned int *)(p + 0x40);
    if (n == 0)
        return 0;
    char **arr = *(char ***)(p + 0x4c);
    for (unsigned int i = 0; i < n; ++i) {
        char *entry = *(char **)((char *)arr + i * 4);
        char *q = *(char **)(entry + 4);
        if (q != 0) {
            unsigned char b = *(unsigned char *)(q + 0x50);
            if ((b & 0x11) == 0)
                return 1;
        }
    }
    return 0;
}