struct S {
    unsigned char pad[0x5d9];
    unsigned char x;
};

extern "C" unsigned char func_6130e5f8(const struct S *s) {
    return (s->x >> 2) & 1;
}