extern "C" int func_6004971c(char *p);

extern "C" int func_600b7080(char *p)
{
    unsigned char v = *(unsigned char *)(p + 0x1054);
    int r = func_6004971c(p);
    return (v == r) ? 1 : 0;
}