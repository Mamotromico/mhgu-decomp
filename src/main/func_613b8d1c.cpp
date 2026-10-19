struct S {
    unsigned int pad;
    unsigned int value;
};

extern "C" void func_613b8d1c(S* p, unsigned int v) {
    if (p->value != v)
        p->value = v;
}