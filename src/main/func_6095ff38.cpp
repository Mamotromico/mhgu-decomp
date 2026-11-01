struct Src {
    int f0;
    int f4;
    int f8;
};

struct Dst {
    char pad0[0xb0];
    int b0;
    int b4;
    int b8;
    int bc;
};

extern "C" void func_6095ff38(Dst *d, const Src *s) {
    d->b0 = s->f0;
    d->b4 = s->f4;
    d->b8 = s->f8;
    d->bc = 0;
}