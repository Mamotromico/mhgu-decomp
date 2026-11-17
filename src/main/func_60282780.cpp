extern "C" int func_60282780(char *p)
{
    int r = *(int *)(p + 0x2634);
    if (r == 0) {
        return r;
    }
    int *v = *(int **)((char *)r + 0x0);
    int (*fn)(void) = *(int (**)(void))((char *)v + 0x15c);
    return fn();
}