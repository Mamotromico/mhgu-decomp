extern "C" void func_6061d188(char *p, const int *in, unsigned char a, unsigned char b, unsigned char c)
{
    unsigned idx = *(unsigned *)(p + 0x40c);
    if (idx > 7) return;
    char *e = p + idx * 0x20;
    *(unsigned *)(e + 0x420) = in[0];
    *(unsigned *)(e + 0x424) = in[1];
    *(unsigned *)(e + 0x428) = in[2];
    *(unsigned char *)(e + 0x430) = a;
    *(unsigned char *)(e + 0x431) = b;
    *(unsigned char *)(e + 0x432) = c;
    *(unsigned *)(p + 0x40c) = idx + 1;
}