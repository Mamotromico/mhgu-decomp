extern "C" void func_60675dc4(void *);
extern "C" void *func_6065cb3c(void *, int);
extern "C" void func_605f3d24(void *);

extern "C" void func_6079cb94(void *p)
{
    func_60675dc4(p);
    void *r = func_6065cb3c(p, 0x20);
    if (r)
        func_605f3d24(r);
}