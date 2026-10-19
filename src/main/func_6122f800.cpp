struct S {
    double d;
    int i;
};

extern "C" void func_6122f800(S *s, double d) {
    s->d = d;
    s->i = 2;
}