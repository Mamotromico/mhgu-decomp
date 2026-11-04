struct dest_t {
    char pad0[0x474];
    unsigned int f474;
    char pad1[0x4d0 - 0x478];
    unsigned int src[8];
};

extern "C" void func_60c6b790(dest_t *d, unsigned int a, unsigned int b, const unsigned int *s) {
    d->f474 = (a & 0xFFFF) | (b << 16);
    for (int i = 0; i < 8; i++) {
        ((unsigned int *)((char *)d + 0x4d0))[i] = s[i];
    }
}