struct S {
    unsigned char pad[0x241];
    unsigned char b;
};

extern "C" unsigned char func_600e92b8(const S *s, int x) {
    if (x != 1)
        return 2;
    return s->b == 0 ? 3 : 2;
}