extern "C" unsigned int func_601ac4d8(unsigned int a, unsigned int b, unsigned int c, unsigned int d, volatile unsigned int e)
{
    unsigned int p = a + b * 24;
    unsigned int v = e;
    p += c * 4;
    p += d * 2;
    *(unsigned short *)(p + 0x12c) = (unsigned short)v;
    return p;
}