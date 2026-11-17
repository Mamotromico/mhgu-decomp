extern "C" void func_60a5b2b8(void *);
extern "C" void func_60a67ecc(void *, void *);

extern "C" void func_60ab1b58(void *self)
{
    char *p = (char *)self;
    func_60a5b2b8(self);
    void *q = *(void **)(p + 0x34);
    func_60a67ecc(self, (char *)q + 0x1b0);
}