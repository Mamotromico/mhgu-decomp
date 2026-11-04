extern "C" int func_606bb7ac(unsigned char *p, int a1)
{
    int r2;
    if (a1 < 0) {
        r2 = p[0x56];
        if (r2 == 0)
            return 0;
        a1 += r2;
        p[0x56] = (unsigned char)a1;
        r2 = 1;
        *(unsigned int *)(p + 0x4c) |= 0x200000;
        return r2;
    }
    r2 = 0;
    if (a1 == 0)
        return r2;
    unsigned int r3 = p[0x56];
    if (r3 > 0x2f)
        return r2;
    a1 += r3;
    p[0x56] = (unsigned char)a1;
    r2 = 1;
    *(unsigned int *)(p + 0x4c) |= 0x200000;
    return r2;
}