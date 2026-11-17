extern "C" unsigned long strlen(const char *);

struct S {
    char pad0[4];
    unsigned *p4;
    unsigned long len8;
};

extern "C" void func_6083e248(S *s, char *str)
{
    s->p4 = (unsigned *)str;
    s->len8 = strlen(str);
}