struct S {
    char pad0[0x40];
    unsigned int f40;
    char pad1[0x2c];
    unsigned int f70;
};

extern "C" unsigned int *func_6137fa8c(unsigned int *out, struct S *s, unsigned int v) {
    if (s->f70 == 2) {
        s->f40 = v;
        *out = 0;
    } else {
        *out = 0x10c08;
    }
    return out;
}