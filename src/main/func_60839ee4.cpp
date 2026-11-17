extern "C" char D_61787f90[];

struct S {
    char *p;
    unsigned char b;
    char pad[3];
};

extern "C" void func_60839ee4(S *s)
{
    s->p = &D_61787f90[8];
    s->b = 0;
}