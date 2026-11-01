extern "C" unsigned int func_6009dc70(const unsigned char *p, const unsigned char *q)
{
    unsigned char v = p[0x7583];
    unsigned int mask = 0x600;
    if (v == 1)
        mask = 0x400;
    if (v == 0)
        mask = 0x200;
    unsigned short h = *(const unsigned short *)(q + 0xa);
    return mask & h;
}