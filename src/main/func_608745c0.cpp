extern "C" int func_60b24e74(void *);
extern "C" int func_60b2cb9c(void *, void *);

extern "C" int func_608745c0(void *self, void *arg)
{
    void *p = *(void **)((char *)self + 0x10);
    void *q = *(void **)((char *)p + 0x8);
    func_60b24e74(q);
    void *r = *(void **)((char *)self + 0x10);
    return func_60b2cb9c(r, arg);
}