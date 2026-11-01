extern "C" int func_61122598(char *p) {
    char *q = *(char **)(p + 0x3ac4);
    unsigned char a = *(unsigned char *)(q + 0);
    if (a != 0) {
        unsigned char b = *(unsigned char *)(q + 0x34c);
        if (b != 0)
            return 1;
    }
    return 0;
}