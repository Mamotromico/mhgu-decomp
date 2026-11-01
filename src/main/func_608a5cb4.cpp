extern "C" void func_608a5cb4(char *dst, const char *src)
{
    struct Src { int a; int b; int c; };
    struct Dst { char pad[0x90]; int a; int b; int c; int d; };
    const struct Src *s = (const struct Src *)src;
    struct Dst *d = (struct Dst *)dst;
    d->a = s->a;
    d->b = s->b;
    d->c = s->c;
    d->d = 0;
}