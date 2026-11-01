extern "C" int func_6138e864(const char *p) {
    if (*(const int *)(p + 0xac) != 2)
        return 0;
    unsigned int v = *(const unsigned int *)(p + 0x98);
    unsigned int d = v - 2;
    if (d < 3)
        return 1;
    return 0;
}