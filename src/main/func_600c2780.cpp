extern "C" void func_6009ce40(void *, unsigned);

extern "C" void func_600c2780(char *p, unsigned v)
{
    unsigned *q = *(unsigned **)(p + 0x1428);
    *(unsigned *)((char *)q + 0x5e34) = v;
    func_6009ce40(p, 0x40);
}