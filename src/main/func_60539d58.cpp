extern "C" void func_608879ac(void);

extern "C" void func_60539d58(char *p)
{
    func_608879ac();
    unsigned v = *(unsigned *)(p + 0x10);
    v = (v & ~(1u << 5)) | (0u << 5);
    *(unsigned *)(p + 0x10) = v;
}