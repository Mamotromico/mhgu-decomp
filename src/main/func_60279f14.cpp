extern "C" char *func_6027a014(void);

extern "C" void func_60279f14(char *p, unsigned char v)
{
    p[0x69] = v;
    char *q = func_6027a014();
    if (q != 0)
        q[0x2739] = v;
}