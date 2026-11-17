extern "C" void func_60966880(void *, int);

extern "C" void func_602a0728(char *p)
{
    void *v = *(void **)(p + 0x26f0);
    if (v == 0)
        return;
    func_60966880(v, 0);
}