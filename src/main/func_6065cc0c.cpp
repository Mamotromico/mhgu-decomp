extern "C" void func_6056e04c(void *);

struct S {
    char pad[0x34];
    void **arr;
};

extern "C" void *func_6055cc0c(S *s, int i)
{
    void *p = s->arr[i];
    if (p)
        func_6056e04c(p);
    return p;
}