extern "C" int func_60123ae0(void *self, void *arg)
{
    char *s = (char *)self;
    void **q = (void **)arg;
    void *p = *q;
    int (*fn)(void *) = *(int (**)(void *))((char *)p + 0xc);
    int r = fn(arg);
    *(int *)(s + 4) = r;
    return r;
}