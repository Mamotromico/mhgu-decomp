extern "C" int func_60a5b2b8(void *);

extern "C" int func_60a67ecc(void *, void *);

extern "C" int func_60a7f1e8(void *p)
{
    func_60a5b2b8(p);
    void *q = *(void **)((char *)p + 0x34);
    return func_60a67ecc(p, (char *)q + 0x1c0);
}