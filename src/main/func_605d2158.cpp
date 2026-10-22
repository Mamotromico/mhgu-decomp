extern "C" void func_605d2158(int *base, int i, char c, int v) {
    int *p = base + i * 3;
    *(char *)((char *)p + 0x54) = c;
    *(int *)((char *)p + 0x50) = v;
}