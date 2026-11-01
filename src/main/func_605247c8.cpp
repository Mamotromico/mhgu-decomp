extern "C" int func_605247c8(char *base, int a, unsigned int b) {
    char *p = base + (a * 3) * 32;
    p = p + (b >> 5) * 4;
    int v = *(int *)(p + 0xdd8);
    unsigned int bit = 1u << (b & 0x1f);
    int r = v & (int)bit;
    return r != 0 ? 1 : 0;
}