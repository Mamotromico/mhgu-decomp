extern "C" void func_6011e29c(void *self, void *ctx)
{
    void *obj = *(void **)ctx;
    int (*fn)(void *) = *(int (**)(void *))((char *)obj + 0xc);
    *(int *)((char *)self + 0x4) = fn(ctx);
}