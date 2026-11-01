extern "C" void func_6054ee34(void *p, unsigned short a1, unsigned int a2)
{
    char *b = (char *)p;
    *(unsigned short *)(b + 0x14) = a1;
    unsigned char r3 = *(unsigned char *)(b + 0xe);
    int r1 = (int)a1 + r3 - 1;
    r1 = r1 / (int)r3;
    *(unsigned short *)(b + 0x12) = (unsigned short)r1;
    *(unsigned short *)(b + 0x10) = 0;
    *(unsigned int *)(b + 0x1c) = a2;
    *(unsigned char *)(b + 0x20) = 1;
}