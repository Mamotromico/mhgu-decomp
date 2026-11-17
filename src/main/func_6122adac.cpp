extern "C" void func_6122adac(void *p)
{
    if (p == 0)
        return;
    void (**slot)(void) = (void (**)(void))((char *)p - 0xc);
    void (*fn)(void) = *slot;
    if (fn == 0) {
        extern void free(void *);
        free((char *)p - 0xc);
        return;
    }
    fn();
}