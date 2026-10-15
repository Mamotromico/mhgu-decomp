struct S6134 {
    char pad[0x10];
    unsigned long long v;
};

extern "C" unsigned long long func_6134efd4(S6134 *p) {
    return p->v;
}