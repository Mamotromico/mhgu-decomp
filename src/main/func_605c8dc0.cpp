extern "C" void func_6056e3b0(void *);
extern "C" void func_6056e61c(void *, int);

extern "C" void func_605c8dc0(void *p)
{
    *(unsigned *)((char *)p + 0x28) = 0x24;
    func_6056e3b0(p);
    func_6056e61c(p, 6);
}