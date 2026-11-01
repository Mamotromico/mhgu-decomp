extern "C" struct S {
    char pad0[0x8];
    unsigned char f8;
    char pad9[0x10 - 0x9];
    unsigned char f10;
    char pad11[0x14 - 0x11];
    int f14;
    int f18;
    int f1c;
    char pad20[0x25 - 0x20];
    unsigned char f25;
    unsigned char f26;
};

extern "C" void func_6121ad40(S *p) {
    p->f10 = 0;
    p->f8 = 0;
    p->f14 = 0;
    p->f18 = 0;
    p->f1c = 0;
    p->f25 = 0;
    p->f26 = 0xff;
}