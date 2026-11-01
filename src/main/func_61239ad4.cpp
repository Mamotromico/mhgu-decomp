struct S1 {
    char pad0[0x10];
    unsigned int f10;
    char pad14[0x4];
    unsigned int f18;
    unsigned char f1c;
    unsigned char f1d;
    unsigned char f1e;
};

struct S0 {
    char pad0[0x4];
    unsigned char f4;
    char pad5[0x3];
    struct S1 *f8;
    unsigned int fc;
};

extern "C" void func_61239ad4(struct S0 *p)
{
    struct S1 *q = p->f8;
    q->f10 = 0;
    q->f18 = 0;
    q->f1d = 0;
    q->f1e = 0;
    q->f1c = q->f1c & 0x4;
    p->f4 = 0;
    p->fc = 0;
}