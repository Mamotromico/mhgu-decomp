extern "C" void func_607c5e4c(void *dst, void *a, void *b, void *c);

extern "C" void func_6001c380(void *p, void *q)
{
    if (!q)
        return;
    void *a = (char *)p + 0x40;
    void *b = (char *)p + 0x60;
    void *c = (char *)p + 0x50;
    func_607c5e4c(q, a, b, c);
}