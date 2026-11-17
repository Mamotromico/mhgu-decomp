extern "C" char D_61767a9c[];

struct S {
    char *p0;
    unsigned short h4;
    unsigned short pad6;
    unsigned int w8;
    unsigned int wc;
};

extern "C" void *func_604b4c38(S *s)
{
    s->p0 = &D_61767a9c[8];
    s->h4 = 0;
    s->w8 = 0;
    s->wc = 0;
    return s;
}