extern "C" void func_60523150(unsigned char *p, int x) {
    int v = *(int *)(p + 0x24) + x;
    if (v > 0x98967f)
        v = 0x98967f;
    if (v <= 0)
        v = 0;
    *(int *)(p + 0x24) = v;
}