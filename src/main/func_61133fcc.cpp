extern "C" int func_61133fcc(char *a) {
    char *p = *(char **)(a + 0x3328);
    if (*(unsigned char *)(p + 0x5e8) == 0)
        return 1;
    char *q = *(char **)(p + 0x6f0);
    int r = (int)*(char **)(q + 0x1470);
    return r != 0 ? 1 : 0;
}