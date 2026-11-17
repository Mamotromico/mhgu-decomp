extern "C" void *func_6065cb3c(void *, unsigned);

extern "C" void func_606787c0(void *p, void *q)
{
    char *r = (char *)func_6065cb3c(p, 0x20);
    if (r)
        *(void **)(r + 0x50) = q;
}