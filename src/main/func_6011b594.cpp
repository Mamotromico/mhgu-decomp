extern "C" void func_6011b594(void *self, void *arg)
{
    void *obj = *(void **)arg;
    int (*fn)(void *) = *(int (**)(void *))((char *)obj + 0xc);
    *(int *)((char *)self + 0x4) = fn(arg);
}