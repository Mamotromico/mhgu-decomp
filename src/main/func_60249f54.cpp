extern "C" void func_6024987c(void *);

extern "C" void func_60249f54(char *p)
{
    func_6024987c(p);
    *(unsigned *)(p + 0x100) = 1;
    unsigned v = *(unsigned *)(p + 0x10);
    v = (v & ~0x30cu) | 0xcu;
    *(unsigned *)(p + 0x10) = v;
}