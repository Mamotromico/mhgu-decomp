extern "C" int func_603abb3c(unsigned char *p)
{
    unsigned short a, b, c;
    if (*(unsigned char *)(p + 0x55) != 0)
        return 0;
    b = *(unsigned short *)(p + 0x1662);
    a = *(unsigned short *)(p + 0x1660);
    a = a | b;
    c = *(unsigned short *)(p + 0x1664);
    c = a | c;
    return (unsigned short)c != 0;
}