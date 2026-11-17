extern "C" void func_6056e4d8(void *);
extern "C" void func_605722e4(void *);
extern "C" void func_60572358(void *);

extern "C" void func_605722bc(void *p)
{
    func_6056e4d8(p);
    func_605722e4(p);
    func_60572358(p);
    *(unsigned *)((char *)p + 0x74) = 0;
}