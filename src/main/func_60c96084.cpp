extern "C" void func_60c96084(char *p)
{
    unsigned int *w = (unsigned int *)p;
    unsigned int r1 = 0;
    w[0x80 / 4] = r1;
    unsigned int r2 = w[0x68 / 4];
    w[0x74 / 4] = r2;
    unsigned int r3 = w[0x6c / 4];
    w[0x78 / 4] = r3;
    w[0x04 / 4] = r2;
    w[0x08 / 4] = r3;
    w[0x0c / 4] = r1;
    *(unsigned char *)(p + 0x10) = (unsigned char)r1;
    w[0x64 / 4] = 1;
}