extern "C" int func_60544450(char *p) {
    int result = 0;
    void *node = *(void **)(p + 0xf4);
    if (node == 0)
        return result;
    node = *(void **)((char *)node + 0x60);
    while (node != 0) {
        unsigned char flags = *(unsigned char *)((char *)node + 0x54);
        if ((flags & 3) != 0) {
            result = 1;
            return result;
        }
        node = *(void **)((char *)node + 0x64);
    }
    return result;
}