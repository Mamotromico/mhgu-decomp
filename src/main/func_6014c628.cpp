struct Src {
    unsigned char pad0[0x1c];
    int f1c;
    int f20;
    int f24;
    int f28;
};

struct Dst {
    unsigned char pad0[0x64];
    int f64;
    int f68;
    int f6c;
    unsigned char pad70[4];
    int f74;
};

extern "C" void func_6014c628(Dst *d, Src *s) {
    d->f64 = s->f1c;
    d->f68 = s->f20;
    d->f6c = s->f24;
    d->f74 = s->f28;
}