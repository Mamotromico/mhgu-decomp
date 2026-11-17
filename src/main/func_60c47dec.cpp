extern "C" void func_60c47dec(unsigned char *p, unsigned char v, int i)
{
    if (i != -1) {
        unsigned n = *(unsigned *)(p + 0xbc);
        if (!(n <= (unsigned)i)) {
            unsigned *tbl = *(unsigned **)(p + 0xc8);
            unsigned char *q = (unsigned char *)tbl[i];
            if (q != 0)
                q[5] = v;
        }
    }
}