struct S {
    unsigned char pad0[4];
    unsigned short f4;
    unsigned char pad1[2];
    unsigned short f8;
};

extern "C" void func_600db080(S *p) {
    p->f8 = 0;
    p->f4 &= 0x83ff;
}