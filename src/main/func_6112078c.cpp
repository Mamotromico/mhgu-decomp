extern "C" int func_600c9eb0(void);

extern "C" void func_6112078c(char *p)
{
    func_600c9eb0();
    unsigned *q = (unsigned *)(p + 0x1408);
    unsigned v = *q;
    *q = v | 0x1000;
    (void)q;
}