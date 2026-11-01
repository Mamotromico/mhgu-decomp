struct S {
    int a;                 // +0x00
    unsigned char b;       // +0x04
    unsigned char pad0[3]; // +0x05
    int c;                 // +0x08
    unsigned char d;       // +0x0c
    unsigned char pad1[3]; // +0x0d
    int e;                 // +0x10
};

extern "C" void func_6121a878(S *p) {
    p->a = 0;
    p->b = 0;
    p->c = -1;
    p->d = 0;
    p->e = 0;
}