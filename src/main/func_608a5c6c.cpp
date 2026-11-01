extern "C" {

struct Src {
    char pad0[0x40];
    int f40;
    int f44;
    int f48;
};

struct Dst {
    int f0;
    int f4;
    int f8;
    int fc;
};

void func_608a5c6c(Dst *d, Src *s) {
    d->f0 = s->f40;
    d->f4 = s->f44;
    d->f8 = s->f48;
    d->fc = 0;
}

}