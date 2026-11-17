extern "C" int func_60552f3c(char *p)
{
    if (p == 0)
        return 0;
    unsigned v = *(unsigned *)(p + 0x2844);
    int r = 4;
    if (!(v & 0x200000)) {
        r = 3;
        if (!(v & 0x100000)) {
            r = 2;
            if (!(v & 0x80000))
                r = (v >> 14) & 1;
        }
    }
    return r;
}