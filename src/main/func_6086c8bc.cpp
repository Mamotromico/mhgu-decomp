extern "C" {
extern char D_617890dc[];
}

struct S {
    void *p0;
    unsigned char b4;
    unsigned char b5;
    char pad6[2];
    void *p8;
};

extern "C" S *func_6086c8bc(S *s) {
    s->p0 = D_617890dc + 0x8;
    s->b4 = 0;
    s->b5 = 1;
    s->p8 = (void *)1;
    return s;
}