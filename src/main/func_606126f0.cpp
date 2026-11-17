extern "C" void func_6056dc28(void *);

extern "C" void func_606126f0(void *p)
{
    func_6056dc28(p);
    void *q = *(void **)((char *)p + 0x4c);
    if (q) {
        void **vtable = *(void ***)q;
        ((void (*)(void *))vtable[6])(q);
    }
}