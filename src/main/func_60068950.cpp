extern "C" void func_60068950(char *p, unsigned idx)
{
    if (idx > 5)
        return;
    char *q = p + idx * 8;
    *(unsigned *)(q + 0x254c) = 0;
    *(unsigned char *)(q + 0x2550) = idx;
    *(unsigned char *)(q + 0x2551) = 0;
    *(unsigned short *)(q + 0x2552) = 0;
}