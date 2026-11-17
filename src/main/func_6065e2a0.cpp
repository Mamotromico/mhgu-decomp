extern "C" void *func_6065cb3c(void *, int);

extern "C" int func_6065e2a0(void *p)
{
    void *r = func_6065cb3c(p, 3);
    int v = 3;
    if (r)
        v = *(int *)((char *)r + 0x54);
    return v;
}