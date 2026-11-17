extern "C" char *func_6027a014(void *, void *);

extern "C" void func_60279f5c(void *a, unsigned b)
{
    *(unsigned *)((char *)a + 0x70) = b;
    char *r = func_6027a014(a, (void *)b);
    if (r)
        *(unsigned char *)(r + 0x1060) = (unsigned char)b;
}