extern "C" void func_6009ce28(void *, unsigned);

extern "C" void func_6111c6d0(char *p)
{
    func_6009ce28(p, 4);
    *(unsigned *)(p + 0xcaf0) = 0;
}