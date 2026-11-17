extern "C" int func_600491f8(int);

extern "C" float func_600bd7e0(char *p) {
    unsigned short v = *(unsigned short *)(p + 0xb5f0);
    int r = func_600491f8(v);
    return (float)r;
}