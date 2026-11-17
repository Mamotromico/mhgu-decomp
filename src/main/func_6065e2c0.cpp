extern "C" int func_6065cb3c(int, int);

extern "C" int func_6065e2c0(int a) {
    int *r = (int *)func_6065cb3c(a, 3);
    if (r)
        return *(int *)((char *)r + 0x58);
    return 2;
}