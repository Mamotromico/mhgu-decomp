extern "C" void func_6080c234(void *);

extern "C" void func_6085fa80(char *p)
{
    if (p == 0)
        return;
    __builtin_memset(p, 0, 0x1a4);
    func_6080c234(p + 0x1a4);
}