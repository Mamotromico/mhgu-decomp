struct S {
    unsigned char pad0[8];
    unsigned short f8;
    unsigned char pad1[2];
    unsigned short f12;
};

extern "C" void func_6018b1c4(S* s, unsigned short a, unsigned short b) {
    s->f12 = a;
    s->f8 = b;
}