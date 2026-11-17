extern "C" unsigned func_60071284();

struct S {
    char pad[0x1428];
    unsigned *p;
};

extern "C" void func_6009ce0c(S *s) {
    unsigned r = func_60071284();
    unsigned *q = *(unsigned **)((char *)s + 0x1428);
    *(unsigned *)((char *)q + 0x3a8) = r;
}