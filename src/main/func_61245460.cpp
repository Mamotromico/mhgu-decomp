extern "C" unsigned func_61245460(char *p)
{
    void (**vt)(void) = *(void (***)(void))p;
    void (*fn)(void *) = *(void (**)(void *))(*(char **)p + 0x3c);
    fn(p);
    return *(unsigned *)(p + 0x28);
}