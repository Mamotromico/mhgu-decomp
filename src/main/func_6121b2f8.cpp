extern "C" void func_6121b2f8(char *p, unsigned char b, unsigned int w)
{
    p[0xc] = (char)b;
    *(unsigned char *)(p + 0x4) = 0;
    *(unsigned int *)(p + 0x10) = 0;
    *(unsigned int *)(p + 0x8) = w;
    *(unsigned int *)(p + 0x14) = 0;
    *(unsigned int *)(p + 0x18) = 0;
    *(unsigned char *)(p + 0x25) = 0;
    *(unsigned char *)(p + 0x26) = 0xff;
}