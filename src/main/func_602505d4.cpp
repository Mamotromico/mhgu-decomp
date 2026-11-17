extern "C" void func_602505d4(char *a, char *b)
{
    unsigned v = *(unsigned *)(b + 0x0);
    unsigned *p = (unsigned *)v;
    int (*fn)(char *) = (int (*)(char *))p[2];
    int r = fn(b);
    *(unsigned short *)(a + 0x4) = (unsigned short)r;
}