extern "C" int func_6060d6c0(void *self, unsigned idx)
{
    char *base;
    unsigned char v;
    if (idx > 7)
        return 0;
    base = *(char **)((char *)self + 0x9c);
    base += idx * 8;
    v = *(unsigned char *)(base + 0x5);
    return v != 0 ? 1 : 0;
}