extern "C" int func_6027f590(unsigned char *p)
{
    int r1 = 0;
    unsigned char r2 = *(unsigned char *)(p + 0x13cc);
    if (r2 & 1) {
        unsigned short h = *(unsigned short *)(p + 0x13f8);
        r1 = 1;
        if (!(h & 0x5f0)) {
            unsigned char b = *(unsigned char *)(p + 0x1406);
            if (b != 0)
                r1 = 1;
            else
                r1 = 0;
        }
    }
    return r1;
}