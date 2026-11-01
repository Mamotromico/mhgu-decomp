extern "C" int func_6055bd6c(void *self, int idx)
{
    char *s = (char *)self;
    void *p = *(void **)(s + 0x5c);
    void *q = *(void **)p;
    if (q == 0)
        return 0;
    void *list = *(void **)q;
    void *e = *(void **)((char *)list + idx * 4);
    if (e == 0)
        return 0;
    return *(int *)((char *)e + 0x88);
}