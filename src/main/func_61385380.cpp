extern "C" int func_6130a814(int);

extern "C" char D_62145a64[];

struct S0 { char pad0[0x144]; int field_144; };

extern "C" int func_61385380(void)
{
    char *p = D_62145a64;
    int *q = *(int **)p;
    struct S0 *s = (struct S0 *)q;
    int r = func_6130a814(s->field_144 + 4);
    return r + 4;
}