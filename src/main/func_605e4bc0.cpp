extern "C" int func_60545bcc(unsigned char *p, int r1, int r2);

extern "C" int func_605e4bc0(unsigned char *p, int a1)
{
    return func_60545bcc(*(unsigned *)(p + 0x24) == 0 ? (unsigned char *)0 : (unsigned char *)*(unsigned *)(p + 0x24), 0, a1);
}