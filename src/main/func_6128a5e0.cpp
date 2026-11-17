extern "C" void func_612297ec(void);

extern "C" void func_6128a5e0(unsigned char *p)
{
    unsigned *q = (unsigned *)(p + 0x8);
    if (*q)
    {
        func_612297ec();
        *q = 0;
    }
}