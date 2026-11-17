extern "C" void func_60a5b2b8(void *);
extern "C" void func_60a67ecc(void *, void *);

extern "C" void func_60a8e8c8(unsigned char *p)
{
    func_60a5b2b8(p);
    unsigned *q = *(unsigned **)(p + 0x34);
    func_60a67ecc(p, (unsigned char *)q + 0x60);
}