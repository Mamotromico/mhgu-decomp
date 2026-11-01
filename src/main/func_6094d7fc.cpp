extern "C" void func_6094d7fc(char *dst, const char *src)
{
    struct Src { int a; int b; int c; };
    struct Dst {
        char pad0[0x70];
        int a;
        int b;
        int c;
        int d;
    };
    const struct Src *s = (const struct Src *)src;
    struct Dst *d = (struct Dst *)dst;
    d->a = s->a;
    d->b = s->b;
    d->c = s->c;
    d->d = 0;
}