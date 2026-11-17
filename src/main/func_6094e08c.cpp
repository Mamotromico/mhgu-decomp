struct Src { unsigned w0; unsigned w1; unsigned w2; };
struct Dst { char pad[0x80]; unsigned w[4]; };

extern "C" void func_6094e08c(Dst *d, const Src *s)
{
    unsigned a = s->w0;
    unsigned b = s->w1;
    unsigned c = s->w2;
    d->w[0] = a;
    d->w[1] = b;
    d->w[2] = c;
    d->w[3] = 0;
}