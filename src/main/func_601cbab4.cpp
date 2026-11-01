extern "C" void func_601cbab4(const char *src, char *dst)
{
    struct Src {
        char pad0[4];
        unsigned short a;
        unsigned short b;
        unsigned short c;
        unsigned short d;
    };
    struct Dst {
        unsigned short a;
        unsigned short b;
        unsigned short c;
        unsigned short d;
    };
    const Src *s = (const Src *)src;
    Dst *d = (Dst *)dst;
    d->a = s->a;
    d->b = s->b;
    d->c = s->c;
    d->d = s->d;
}