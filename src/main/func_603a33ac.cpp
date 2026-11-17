extern "C" int func_6039cadc(char *, int);

extern "C" int func_603a33ac(char *p) {
    char *a = *(char **)(p + 0xac);
    if (a == 0) return 0;
    char *b = *(char **)(a + 0x30);
    if (b == 0) return 0;
    return func_6039cadc(b, 0);
}