struct S {
    char pad0[0x6c];
    float f;
    char pad1[0x54];
    unsigned char a;
    unsigned char b;
};

extern "C" void func_60c17b58(S* p, unsigned char a, unsigned char b, float f) {
    p->a = a;
    p->b = b;
    p->f = f;
}