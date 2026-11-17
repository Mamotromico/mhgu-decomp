extern "C" void func_6056df00(void *);

extern "C" void *func_6065cbe8(void *self, int idx)
{
    void **arr = *(void ***)((char *)self + 0x34);
    void *p = arr[idx];
    if (p)
        func_6056df00(p);
    return p;
}