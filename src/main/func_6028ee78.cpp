extern "C" void func_6028c9f0(void *);
extern "C" void func_60283a0c(void *, void *, void *);

extern "C" void func_6028ee78(void *p)
{
    func_6028c9f0(p);
    void *b = (char *)p + 0x273c;
    void *a = (char *)p + 0x2738;
    func_60283a0c(p, b, a);
}