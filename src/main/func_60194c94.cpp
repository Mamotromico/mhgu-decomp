extern "C" void func_60194c94(unsigned char *base, unsigned short *p)
{
    if (p == 0)
        return;
    unsigned short v = *(unsigned short *)((char *)p + 4);
    unsigned char *byte = base + (v >> 3);
    unsigned int bit = 1u << (v & 7);
    byte[0x50] = (unsigned char)(byte[0x50] | bit);
}