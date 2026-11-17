extern "C" void func_6032a400(void *);

extern "C" void func_604913bc(char *p)
{
    unsigned *q = (unsigned *)(p + 0x15b0);
    unsigned v = *q;
    if (v == 0)
        return;
    func_6032a400((void *)v);
    *q = 0;
}