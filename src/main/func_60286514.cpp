extern "C" void *func_600df814(unsigned *, int);

extern "C" int func_60286514(char *a)
{
    unsigned *p = *(unsigned **)(a + 0x13c4);
    unsigned char *q = (unsigned char *)func_600df814(p + 1, 0);
    return (q[0x10] >> 1) & 1;
}