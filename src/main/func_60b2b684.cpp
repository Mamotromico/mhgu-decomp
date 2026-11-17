extern "C" void func_60873eec(void *);

extern "C" int func_60b2b684(char *p)
{
    func_60873eec(p + 0xe0);
    unsigned *a = *(unsigned **)(p + 0x14);
    unsigned *b = *(unsigned **)(a + 0x0);
    int (*fn)(unsigned *) = (int (*)(unsigned *))*(unsigned **)((char *)b + 0x18);
    return fn(a);
}