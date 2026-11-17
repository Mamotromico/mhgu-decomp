extern "C" void *func_612a222c(unsigned size);

extern "C" void *func_612a45e4(void)
{
    void *r = func_612a222c(8);
    if (!r)
        return 0;
    *(unsigned *)((char *)r + 0x0) = 0;
    *(unsigned *)((char *)r + 0x4) = 0;
    return r;
}