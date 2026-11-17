extern "C" {
extern void *D_618583a8[];
int func_6019463c(void *, void *, void *);
int func_6018afb0(void *a, void *b, void *c)
{
    void *p = *(void **)D_618583a8;
    int r = func_6019463c(p, a, b);
    return r != 0 ? 1 : 0;
}
}