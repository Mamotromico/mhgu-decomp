struct S {
    int f0;
    void *f4;
    int f8;
    int fC;
};

extern "C" S *func_61239d70(S *p) {
    p->f8 = 0;
    p->fC = 0;
    p->f4 = &p->f8;
    return p;
}