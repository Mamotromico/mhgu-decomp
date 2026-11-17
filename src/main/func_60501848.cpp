extern "C" unsigned short *func_60501848(unsigned short *p, int bit)
{
    int one = 1;
    p += 0xD0;
    *p |= one << (bit - 0x32);
    return p;
}