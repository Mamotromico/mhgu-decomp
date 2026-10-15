struct S_601b3540 {
    char pad0[0x14];
    int field14;
    int field18;
};

extern "C" void func_601b3540(S_601b3540 *s, int a, int b) {
    s->field14 = a;
    s->field18 = b;
}