struct S606c24d0 {
    char pad0[0x1900];
    int a;
    int b;
};

extern "C" int func_606c24d0(S606c24d0 *p) {
    return p->a + 12 * p->b;
}