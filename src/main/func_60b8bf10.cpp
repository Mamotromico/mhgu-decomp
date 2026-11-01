extern "C" void func_60b8bf10(char *base, int a, int b, int c)
{
    if (b <= 1) {
        char *p = base + a * 0x1b0 + b;
        p[0x35] = (char)0xff;
    }
    char *q = base + c * 0x1b0;
    q[0x60] = 0;
    q[0x34] = 0;
}