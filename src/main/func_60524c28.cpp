extern "C" {
struct S {
    char pad0[0x2c94];
    unsigned int words[8];
};
unsigned int func_60524c28(S *s, unsigned int bit) {
    unsigned int word = *(unsigned int *)((char *)s + 0x3494 + ((bit >> 5) << 2));
    unsigned int mask = 1u << (bit & 0x1f);
    unsigned int v = word & mask;
    return v ? 1u : 0u;
}
}