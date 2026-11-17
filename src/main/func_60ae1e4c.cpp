extern "C" void func_60a5b2b8(unsigned *thisptr);
extern "C" void func_60a67ecc(unsigned *thisptr, unsigned *arg);

extern "C" void func_60ae1e4c(unsigned *thisptr)
{
    func_60a5b2b8(thisptr);
    unsigned *p = (unsigned *)(*(unsigned *)((char *)thisptr + 0x34) + 0x180);
    func_60a67ecc(thisptr, p);
}