extern "C" int func_60ff2614(char *p) {
    unsigned v = *(unsigned *)(p + 0xcafc);
    v = (v & ~1u) | 0;
    return v == 2 ? 1 : 0;
}