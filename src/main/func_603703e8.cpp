struct S {
    char pad0[4];
    unsigned short f4;
    unsigned short f6;
    unsigned short f8;
    char padA[2];
    unsigned int fC;
    unsigned short f10;
    unsigned short f12;
    unsigned short f14;
    unsigned short f16;
    unsigned short f18;
    unsigned short f1A;
    unsigned char f1C;
    unsigned char f1D;
    unsigned char f1E;
    unsigned char f1F;
    unsigned char f20;
    unsigned char f21;
    char pad22[0x30 - 0x22];
};

extern "C" void func_603703e8(S* d, const S* s) {
    d->f4 = s->f4;
    d->f6 = s->f6;
    d->f8 = s->f8;
    d->fC = s->fC;
    d->f10 = s->f10;
    d->f1C = s->f1C;
    d->f12 = s->f12;
    d->f1D = s->f1D;
    d->f14 = s->f14;
    d->f1E = s->f1E;
    d->f16 = s->f16;
    d->f1F = s->f1F;
    d->f18 = s->f18;
    d->f20 = s->f20;
    d->f1A = s->f1A;
    d->f21 = s->f21;
}