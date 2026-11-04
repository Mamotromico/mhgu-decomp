extern "C" unsigned int func_6138f4ec(const unsigned char* p)
{
    unsigned int r1 = 0;
    unsigned int r2 = *(const unsigned int*)(p + 0x3c);
    if (r2 != 0) {
        r2 = *(const unsigned int*)(p + 0x70);
        if (r2 == 4) {
            r1 = *(const unsigned char*)(p + 0xc0);
            r2 = 0;
            if (r1 == 0)
                r2 = 1;
            r1 = *(const unsigned int*)(p + (r2 << 2) + 0xd0);
        }
    }
    return r1;
}