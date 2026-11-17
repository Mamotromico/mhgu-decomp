struct Src { unsigned v[3]; };
struct Dst { char pad0[0x40]; unsigned x; unsigned y; unsigned z; unsigned w; };
struct Obj { char pad0[0x150]; Dst *a; Dst *b; };

extern "C" void func_6032a45c(Obj *o, Src *s, int idx)
{
    if (idx > 0)
        return;
    Dst *a = *(Dst **)((char *)o + idx * 4 + 0x150);
    if (a) {
        a->x = s->v[0];
        a->y = s->v[1];
        a->z = s->v[2];
        a->w = 0;
    }
    Dst *b = *(Dst **)((char *)o + idx * 4 + 0x154);
    if (!b)
        return;
    b->x = s->v[0];
    b->y = s->v[1];
    b->z = s->v[2];
    b->w = 0;
}