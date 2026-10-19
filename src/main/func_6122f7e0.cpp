struct S {
    int a;
    int b;
    int c;
};

extern "C" void func_6122f7e0(S *p, int x) {
    S s = { x, x >> 31, 1 };
    *p = s;
}