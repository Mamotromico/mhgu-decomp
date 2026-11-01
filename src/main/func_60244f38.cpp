struct S {
    unsigned short f0;
    unsigned char f2;
    unsigned char f3;
    unsigned int f4;
    unsigned short f8;
};

extern "C" void func_60244f38(volatile S* p) {
    p->f0 = 0xffff;
    p->f2 = 0;
    p->f3 = 0;
    p->f4 = 0;
    p->f8 = 0xffff;
}