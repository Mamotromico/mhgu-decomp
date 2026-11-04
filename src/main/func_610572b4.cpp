extern "C" void func_610572b4(char *p);

extern "C" void func_610572b4(char *p)
{
    unsigned int v = *(unsigned int *)(p + 0xcb3c);
    unsigned int b;
    b = *(unsigned int *)(p + 0xcb38);
    v = b | (v << 2);
    b = *(unsigned int *)(p + 0xcb40);
    v |= b << 4;
    b = *(unsigned int *)(p + 0xcb44);
    v |= b << 6;
    b = *(unsigned int *)(p + 0xcb48);
    v |= b << 8;
    b = *(unsigned int *)(p + 0xcb4c);
    v |= b << 10;
    *(unsigned short *)(p + 0xcb24) = (unsigned short)v;
}