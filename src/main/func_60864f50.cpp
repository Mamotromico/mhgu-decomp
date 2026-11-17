extern "C" char D_61788f70[];

struct S {
    char *p0;
    int f4;
    int f8;
    char pad0c[4];
    int f10;
};

extern "C" void func_60864f50(S *s) {
    s->f4 = 6;
    s->f8 = 0;
    s->f10 = 0;
    s->p0 = &D_61788f70[0] + 8;
}