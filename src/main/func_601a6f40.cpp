extern "C" void func_601a6f40(char *p)
{
    unsigned v = *(unsigned *)(p + 0x128);
    v &= ~(3u << 9);
    *(unsigned *)(p + 0x128) = v;
    *(unsigned short *)(p + 0x12c) = 0;
    *(unsigned char *)(p + 0x12e) = 0;
}