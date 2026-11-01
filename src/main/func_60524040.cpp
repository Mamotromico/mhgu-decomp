extern "C" int func_60524040(void *base, unsigned int bit) {
    unsigned int word = bit >> 5;
    unsigned int b = bit & 0x1f;
    unsigned int *p = (unsigned int *)((char *)base + word * 4);
    unsigned int v = *(unsigned int *)((char *)p + 0xd24);
    return (v >> b) & 1 ? 1 : 0;
}