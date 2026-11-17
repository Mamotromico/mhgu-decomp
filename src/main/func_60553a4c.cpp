extern "C" void func_60553a4c(char *p) {
    unsigned int v = *(unsigned int *)(p + 0x10);
    v &= ~3u;
    *(unsigned int *)(p + 0x10) = v;
}