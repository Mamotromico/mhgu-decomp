extern "C" void func_6056dfac(void *);

extern "C" void *func_6065cbc4(void *p, unsigned i)
{
    void **arr = *(void ***)((char *)p + 0x34);
    void *r = arr[i];
    if (r)
        func_6056dfac(r);
    return r;
}