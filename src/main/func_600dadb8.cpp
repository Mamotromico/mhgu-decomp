extern "C" char *func_600dadb8(char *a, int b, unsigned short c) {
    char *p = a + (b << 1);
    *(unsigned short *)(p + 0xa) = c;
    return p;
}