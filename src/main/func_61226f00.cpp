extern "C" void func_61226f00(void *p)
{
    if (p == 0)
        return;
    void *q = (void *)((char *)p - 8);
    void *fn = *(void **)q;
    if (fn == 0) {
        extern void free(void *);
        free(q);
        return;
    }
    ((void (*)(void *))fn)(q);
}