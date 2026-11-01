struct S {
    char pad0[0xe5c];
    int f0;
    char pad1[0x182];
    unsigned short f1;
};

extern "C" int func_6003b54c(S *s) {
    if (s->f0 == 0)
        return 0;
    return s->f1 != 0;
}