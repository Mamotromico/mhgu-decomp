extern "C" {
    unsigned func_60838750(void *p);
}

extern "C" unsigned func_60cd293c(char *p)
{
    unsigned v = func_60838750(p + 0x50);
    return v - *(unsigned *)(p + 0x30);
}