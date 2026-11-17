extern "C" int func_6039cadc(char *p, int n);

extern "C" int func_603c6124(char *p) {
    char *q = *(char **)(p + 0x1c);
    if (q == 0)
        return 0;
    return func_6039cadc(q, 0);
}