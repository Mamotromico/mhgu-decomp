extern "C" int func_60545bcc(unsigned, int, int);

struct S {
    char pad[0x24];
    unsigned field;
};

extern "C" int func_6062f128(S *p, int arg) {
    int v = (int)p->field;
    return func_60545bcc((unsigned)v, 0x1e, arg);
}