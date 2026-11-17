extern "C" {
extern char D_61767a14[];
}

struct S {
    unsigned *f0;
    unsigned short f4;
    unsigned short pad6;
    unsigned f8;
    unsigned fc;
};

extern "C" void func_604b4734(S *s)
{
    s->f0 = (unsigned *)(&D_61767a14[0x8]);
    s->f4 = 0;
    s->f8 = 0;
    s->fc = 0;
}