extern "C" void func_6054533c(void *, void *, void *);

extern "C" void func_605d2a6c(char *p, void *b)
{
    void *a = *(void **)(p + 0x24);
    void *c = *(void **)(p + 0x2c);
    func_6054533c(a, c, b);
}