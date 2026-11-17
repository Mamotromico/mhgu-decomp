extern "C" void func_60c46d90(int *self, unsigned i, unsigned j, unsigned char v)
{
    unsigned cnt;
    if ((int)i == -1)
        return;
    cnt = *(unsigned *)((char *)self + 0xbc);
    if (cnt <= i)
        return;
    int *p = *(int **)((char *)self + 0xc8);
    int *e = (int *)*(unsigned *)((char *)p + i * 4);
    if (e == 0)
        return;
    unsigned c2 = *(unsigned *)((char *)e + 0x5c);
    if (c2 <= j)
        return;
    int *q = (int *)*(unsigned *)((char *)e + 0x58);
    char *r = (char *)q + j * 0x40;
    if (r == 0)
        return;
    *(unsigned char *)(r + 0xc) = v;
}