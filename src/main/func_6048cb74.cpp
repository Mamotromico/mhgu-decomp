extern "C" int func_6048cb74(int base, char *p) {
    if (p == 0)
        return 0;
    int v = *(int *)(p + 0x1598);
    int s = v << 3;
    int t = s - v;
    int r = base + (t << 2) + 0x6fe8;
    if (v == 0x35)
        r = 0;
    return r;
}