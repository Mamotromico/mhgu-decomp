extern "C" void func_60114e54(void *self, void *arg)
{
    unsigned *a = *(unsigned **)arg;
    unsigned (*fn)(void *) = (unsigned (*)(void *))a[3];
    unsigned r = fn(arg);
    *(unsigned *)((char *)self + 4) = r;
}