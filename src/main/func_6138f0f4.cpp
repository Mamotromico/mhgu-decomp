extern "C" int func_6138f0f4(const unsigned char *p) {
    if (*(const unsigned int *)(p + 0xac) != 0x11)
        return 0;
    int v = *(const int *)(p + 0x98);
    int d = v - 2;
    return (unsigned int)d < 3 ? 1 : 0;
}