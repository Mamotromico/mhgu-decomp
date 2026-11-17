extern "C" unsigned func_600db568(void *p)
{
    unsigned short a = *(unsigned short *)((char *)p + 0xa);
    unsigned short b = *(unsigned short *)((char *)p + 0xc);
    unsigned short c = *(unsigned short *)((char *)p + 0xe);
    unsigned r = (a != 0) + (b != 0) + (c != 0);
    return r;
}