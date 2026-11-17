extern "C" void func_603f7c10(void *);

struct S {
    char pad0[0x34];
    int f34;
    int f38;
    int f3c;
    char pad40[0x5d - 0x40];
    unsigned char f5d;
    char pad5e[0x72 - 0x5e];
    unsigned char f72;
};

extern "C" void func_603f831c(struct S *p)
{
    func_603f7c10(p);
    p->f72 = p->f5d;
    p->f34 = 0;
    p->f38 = 0;
    p->f3c = 0;
}