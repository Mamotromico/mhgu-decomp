extern "C" int func_60b6a288(char *r0, int r1, int *r2);

extern "C" int func_60b6a288(char *r0, int r1, int *r2)
{
    int r3 = *(int *)(r0 + 0xc8);
    if (r3 == 0) {
        r1 = 0;
        r0 = (char *)(r1);
        return (int)r0;
    }
    r3 = *(int *)(r0 + 0x80);
    if ((unsigned)r1 >= (unsigned)r3)
        r1 = r3 - 1;
    if (r2 == 0)
        r2 = (int *)(r0 + 0xac);
    r0 = (char *)r1;
    *r2 = r1;
    return (int)r0;
}