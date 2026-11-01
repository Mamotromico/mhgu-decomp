struct S {
    unsigned char pad0[0x70];
    unsigned char *p;
    unsigned char pad1;
    unsigned char b;
};

extern "C" int func_606efec8(S *s, unsigned int i) {
    unsigned char idx = (unsigned char)i;
    return s->p[idx] == s->b;
}