extern char D_6177be04[];

extern "C" void func_606a76c4(void *, void *);

extern "C" void *func_606a85b4(void *p)
{
    char *base = D_6177be04;
    char **q = (char **)p;
    char *v = base + 8;
    *q++ = v;
    func_606a76c4(q, v);
    return p;
}