extern "C" void func_60b2ac38(char *p)
{
    if (*(unsigned char *)(p + 0xe2))
        return;
    *(unsigned char *)(p + 0xe2) = 1;
    unsigned r2 = *(unsigned *)(p + 0x334);
    unsigned r1 = *(unsigned *)(p + 0x1dc);
    if (r2 != 0)
        r1 = ((r2 << 4) - r2 + r1) >> 4;
    *(unsigned *)(p + 0x334) = r1;
}