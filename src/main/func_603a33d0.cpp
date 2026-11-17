extern "C" int func_6039cadc(void *, int);

extern "C" int func_603a33d0(char *a)
{
    int *p = *(int **)(a + 0xac);
    if (p != 0) {
        p = *(int **)((char *)p + 0x34);
        if (p != 0)
            return func_6039cadc(p, 0);
    }
    return 0;
}