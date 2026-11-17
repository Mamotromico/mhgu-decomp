extern "C" void func_6056e3ac(void *);

extern "C" void func_6063a67c(void *p)
{
    func_6056e3ac(p);
    *(unsigned int *)((char *)p + 0x50) = 0;
    *(unsigned char *)((char *)p + 0x54) = 0;
}