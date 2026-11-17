extern char D_617404b4[];

struct S {
    char *p;
    unsigned short h;
};

extern "C" void func_601bba88(struct S *s)
{
    s->p = &D_617404b4[8];
    s->h = 0;
}