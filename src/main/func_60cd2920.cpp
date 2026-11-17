extern "C" unsigned func_60cd2920(char *p);

extern "C" unsigned func_60838750(void *);

extern "C" unsigned func_60cd2920(char *p)
{
    unsigned r = func_60838750(p + 0x34);
    return r - *(unsigned *)(p + 0x2c);
}