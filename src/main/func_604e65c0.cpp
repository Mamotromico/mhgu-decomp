struct S {
    char pad0[0x1b58];
    unsigned short f1b58;
    unsigned char f1b5a;
    unsigned char f1b5b;
    char pad1[0x1b5e - 0x1b5c];
    unsigned short f1b5e;
    char pad2[0x1b64 - 0x1b60];
    unsigned short f1b64;
    unsigned char f1b66;
    unsigned char f1b67;
    char pad3[0x1b6a - 0x1b68];
    unsigned short f1b6a;
    char pad4[0x1b70 - 0x1b6c];
    unsigned short f1b70;
    unsigned char f1b72;
    unsigned char f1b73;
    char pad5[0x1b76 - 0x1b74];
    unsigned short f1b76;
    char pad6[0x1b7c - 0x1b78];
    unsigned short f1b7c;
    unsigned char f1b7e;
    unsigned char f1b7f;
    char pad7[0x1b82 - 0x1b80];
    unsigned short f1b82;
};

extern "C" void func_604e65c0(S *p)
{
    p->f1b58 = 0;
    p->f1b5a = 0;
    p->f1b5e = 0xffff;
    p->f1b5b = 0;
    p->f1b64 = 0;
    p->f1b66 = 0;
    p->f1b6a = 0xffff;
    p->f1b67 = 0;
    p->f1b70 = 0;
    p->f1b72 = 0;
    p->f1b76 = 0xffff;
    p->f1b73 = 0;
    p->f1b7c = 0;
    p->f1b7e = 0;
    p->f1b82 = 0xffff;
    p->f1b7f = 0;
}