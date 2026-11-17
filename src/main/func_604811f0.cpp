extern "C" int func_600b7068(int, unsigned char);

extern "C" int func_604811f0(char *p) {
    int v = *(int *)(p + 0x1610);
    if (v == 0)
        return 0;
    unsigned char b = *(unsigned char *)(p + 0x1054);
    return func_600b7068(v, b);
}