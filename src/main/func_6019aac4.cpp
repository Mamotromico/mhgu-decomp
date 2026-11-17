extern "C" void func_607af3e4(void *);

extern "C" void func_6019aac4(char *p)
{
    char **slot = (char **)(p + 0x62f0);
    char *q = *slot;
    if (q == 0)
        return;
    func_607af3e4(q);
    *slot = 0;
}