extern "C" int func_6050ad64(void *p) {
    unsigned char *b = (unsigned char *)p;
    unsigned int a = *(unsigned int *)(b + 0x1e4);
    int r0 = 1;
    if (a == 7)
        return r0;
    unsigned int c = *(unsigned int *)(b + 0x1e0);
    r0 = 0;
    if (c == 7)
        r0 = 1;
    return r0;
}