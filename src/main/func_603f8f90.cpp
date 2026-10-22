struct Dest {
    char pad0[0x5c];
    unsigned char f5c;
    unsigned char f5d;
};

struct Src {
    char pad0[0x24];
    unsigned char f24;
    unsigned char f25;
};

extern "C" void func_603f8f90(Dest *d, Src *s) {
    d->f5c = s->f24;
    d->f5d = s->f25;
}