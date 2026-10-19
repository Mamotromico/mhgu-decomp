struct S {
    unsigned int pad;
    unsigned int field;
};

extern "C" void func_6122b22c(S* s, unsigned int v) {
    s->field += v;
}