extern "C" void func_612297ec(void *);

extern "C" void func_6128a7a0(void *self)
{
    char *p = (char *)self;
    void *q = *(void **)(p + 0x8);
    if (q == 0)
        return;
    func_612297ec(q);
    *(unsigned *)(p + 0x8) = 0;
}