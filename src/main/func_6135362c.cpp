struct S {
    unsigned char pad0[4];
    unsigned short a;
    unsigned char pad1[2];
    unsigned int b;
    unsigned short c;
    unsigned char pad2[2];
};

extern "C" void func_6135362c(S* s) {
    s->a = 0;
    s->b = 0;
    s->c = 0;
}