struct S {
    int a;
    int b;
    int c;
};

extern "C" void func_6122f7c0(S *s, int unused, int x, int y) {
    s->a = x;
    s->b = y;
    s->c = 1;
}