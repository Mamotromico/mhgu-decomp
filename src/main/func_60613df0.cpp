extern "C" void func_6056dc28(void *);

extern "C" void func_60613df0(void *self)
{
    func_6056dc28(self);
    void *p = *(void **)((char *)self + 0x54);
    if (p == 0)
        return;
    void *v = *(void **)p;
    void (*fn)(void *) = *(void (**)(void *))((char *)v + 0x18);
    fn(p);
}