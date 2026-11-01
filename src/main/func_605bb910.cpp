extern "C" void func_605bb910(void *p)
{
    unsigned char *b = (unsigned char *)p;
    *(volatile short *)(b + 0x14) = 0;
    *(volatile int *)(b + 0x0) = 0;
    *(volatile int *)(b + 0x4) = 0;
    *(volatile int *)(b + 0x8) = 0;
    *(volatile int *)(b + 0xc) = 0;
    *(volatile int *)(b + 0x10) = 0;
    *(volatile unsigned char *)(b + 0x16) = 1;
}