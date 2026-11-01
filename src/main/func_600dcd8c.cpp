struct S {
    char pad0[4];
    unsigned short f4;
    char pad6[0x0d];
    unsigned char f13;
};

extern "C" unsigned char func_600dcd8c(S *s)
{
    return (s->f4 & 0x1f) == 0x14 ? s->f13 : 0;
}