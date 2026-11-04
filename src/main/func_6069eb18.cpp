extern "C" int func_6069eb18(char *p, int a, int b) {
    unsigned int n = *(unsigned int *)(p + 0x68);
    if (n == 0)
        return 0;
    char **arr = *(char ***)(p + 0x74);
    for (unsigned int i = 0; i < n; i++) {
        char *e = arr[i];
        if (e == 0)
            continue;
        signed char f4 = *(signed char *)(e + 0x4);
        if (f4 == a) {
            signed char f5 = *(signed char *)(e + 0x5);
            if (f5 == b)
                return (int)e;
        }
    }
    return 0;
}