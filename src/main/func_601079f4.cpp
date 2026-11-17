extern "C" void func_601079f4(void *self, void *arg)
{
    void *p = *(void **)arg;
    int (*fn)(void *) = *(int (**)(void *))((char *)p + 0xc);
    int r = fn(arg);
    *(int *)((char *)self + 4) = r;
}