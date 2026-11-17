extern "C" void free(void *);

extern "C" void func_6122c788(void *p)
{
    if (!p)
        return;
    void **q = (void **)((char *)p - 8);
    void *f = *q;
    if (f)
        ((void (*)(void))f)();
    else
        free(q);
}