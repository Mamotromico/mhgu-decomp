extern "C" void func_613ed7d8(char *p)
{
    unsigned int w = *(unsigned int *)(p + 4);
    p[0x10] = (char)(w >> 24);
    p[0x11] = (char)(w >> 16);
    p[0x12] = (char)(w >> 8);
    p[0x13] = (char)w;

    p[0x14] = p[0x8];
    p[0x15] = p[0x9];

    unsigned short h;
    h = *(unsigned short *)(p + 0xa);
    p[0x16] = (char)(h >> 8);
    p[0x17] = (char)h;

    h = *(unsigned short *)(p + 0xc);
    p[0x18] = (char)(h >> 8);
    p[0x19] = (char)h;

    h = *(unsigned short *)(p + 0xe);
    p[0x1a] = (char)(h >> 8);
    p[0x1b] = (char)h;
}