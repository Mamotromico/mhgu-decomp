extern "C" void func_60887648(void *);

extern "C" void func_600709e0(char *p, void *arg)
{
    *(void **)(p + 0x75cc) = arg;
    func_60887648(arg);
}