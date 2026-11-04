extern "C" void func_6054edec(char *obj, unsigned int a, unsigned int b, unsigned int c)
{
    struct S {
        char pad0[0xd];
        unsigned char f0d;
        unsigned char f0e;
        char pad0f[0x2];
        unsigned short f10;
        unsigned short f12;
        unsigned short f14;
        char pad16[0x2];
        unsigned int f18;
        unsigned int f1c;
        unsigned char f20;
    };
    struct S *s = (struct S *)obj;

    *(unsigned short *)(obj + 0x14) = (unsigned short)a;
    *(unsigned char *)(obj + 0xe) = (unsigned char)a;
    *(unsigned short *)(obj + 0x12) = (unsigned short)1;

    unsigned int r3;
    if (c == 1) {
        r3 = *(unsigned char *)(obj + 0xd);
        if (r3 >= a)
            r3 = a + 0xff;
    } else {
        r3 = 0;
    }
    *(unsigned char *)(obj + 0xd) = (unsigned char)r3;

    *(unsigned short *)(obj + 0x10) = (unsigned short)0;
    *(unsigned int *)(obj + 0x18) = b;
    *(unsigned int *)(obj + 0x1c) = 0;
    *(unsigned char *)(obj + 0x20) = (unsigned char)1;
    (void)s;
}