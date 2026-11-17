extern "C" char D_61851ab8[];

extern "C" void *func_607aa47c(void *);

extern "C" void func_6004f03c(void *p)
{
    void *q = func_607aa47c(&D_61851ab8);
    void **a = *(void ***)q;
    void (*fn)(void *, void *) = (void (*)(void *, void *))*(void **)((char *)a + 0x34);
    fn(q, p);
}