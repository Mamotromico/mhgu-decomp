extern "C" void func_612467ec(void *, unsigned);

extern "C" void *func_61239d88(char *p)
{
    unsigned v = *(unsigned *)(p + 0x8);
    func_612467ec(p + 0x4, v);
    return p;
}