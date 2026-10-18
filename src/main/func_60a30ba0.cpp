struct S {
    char pad[12];
    unsigned int f;
};

extern "C" void func_60a30ba0(volatile struct S *p) {
    p->f = 0xFFFFFFFFu;
}