extern "C" {
    extern unsigned char *func_600514b0(unsigned);
}

extern "C" float func_600ca8ec(unsigned char *p)
{
    unsigned r = *(unsigned *)(p + 0xca80);
    unsigned char *q = func_600514b0(r);
    return *(float *)(q + 4);
}