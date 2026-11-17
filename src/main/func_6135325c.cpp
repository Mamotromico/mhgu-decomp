extern "C" void func_6135a9b4(void *);
extern "C" void *memset(void *, int, unsigned);

extern "C" void func_6135325c(void *p)
{
    func_6135a9b4(p);
    memset((char *)p + 0xc, 0, 0x16c);
}