extern "C" {

struct Src {
    int f0;
    int f4;
    int f8;
};

struct Dst {
    char pad0[0xd20];
    int f_d20;
    int f_d24;
    int f_d28;
    int f_d2c;
    char pad1[0xd55 - 0xd30];
    unsigned char f_d55;
};

void func_609d3c2c(Dst* d, const Src* s)
{
    d->f_d20 = s->f0;
    d->f_d24 = s->f4;
    d->f_d28 = s->f8;
    d->f_d2c = 0;
    d->f_d55 = 1;
}

}