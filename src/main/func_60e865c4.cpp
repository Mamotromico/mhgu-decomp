extern "C" void func_600c9eb0(void *);

struct S {
    char pad0[0x170];
    int field170;
};

extern "C" void func_60e865c4(S *p) {
    func_600c9eb0(p);
    p->field170 = 2;
}