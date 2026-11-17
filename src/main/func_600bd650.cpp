extern "C" void func_600bd650(int *p, unsigned short v)
{
    *(volatile unsigned char *)((char *)p[0x1428 / 4] + 0x5d02) = 1;
    *(volatile unsigned short *)((char *)p[0x1428 / 4] + 0x5d00) = v;
}