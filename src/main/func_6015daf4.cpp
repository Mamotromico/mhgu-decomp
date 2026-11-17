extern "C" void func_6015daf4(unsigned char *p)
{
    if (*(unsigned char *)(p + 0x28) != 0) {
        if (*(unsigned char *)(p + 0x2c) <= 2) {
            unsigned v2 = *(unsigned *)(p + 0xe48);
            unsigned v1 = *(unsigned *)(p + 0xe44);
            *(unsigned *)(p + 0x1d14) = v2;
            *(unsigned *)(p + 0x1d10) = v1;
        }
    }
}