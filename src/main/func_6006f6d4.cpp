extern "C" void func_6006f6d4(void *arg, void *ctx)
{
    void *obj = *(void **)((char *)arg + 0x75e4);
    void *vtbl = *(void **)obj;
    void (*method)(void *, void *) = *(void (**)(void *, void *))((char *)vtbl + 0x4c);
    method(obj, ctx);
}