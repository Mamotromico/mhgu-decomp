struct S {
    int a;
    int b;
    int c;
    char pad0c;
    char d;
};

extern "C" void func_61398cf8(S* p) {
    p->d = 0;
    p->a = 0;
    p->b = 0;
    p->c = 0;
}