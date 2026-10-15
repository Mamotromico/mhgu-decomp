struct S {
    char pad[0x7c];
    float f;
};

extern "C" void func_6095ff5c(struct S *p, float f) {
    p->f = f;
}