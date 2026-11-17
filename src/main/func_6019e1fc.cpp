extern "C" void func_6019e1fc(char *base)
{
    unsigned i = 0;
    do {
        char *p = base + i;
        i += 8;
        unsigned h0 = *(unsigned short *)(p + 0x1a);
        unsigned h1 = *(unsigned short *)(p + 0x1c);
        *(unsigned short *)(p + 0xe4) = (unsigned short)h1;
        *(unsigned short *)(p + 0xe2) = (unsigned short)h0;
        unsigned h2 = *(unsigned short *)(p + 0x1e);
        unsigned h3 = *(unsigned short *)(p + 0x20);
        *(unsigned short *)(p + 0xe8) = (unsigned short)h3;
        *(unsigned short *)(p + 0xe6) = (unsigned short)h2;
    } while (i != 0xc8);
}