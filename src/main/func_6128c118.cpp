extern "C" void func_612297ec(void *p);

extern "C" void func_6128c118(void *p)
{
    void *q = *(void **)((char *)p + 0x8);
    if (q == 0)
        return;
    func_612297ec(q);
    *(void **)((char *)p + 0x8) = 0;
}