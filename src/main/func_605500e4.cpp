extern "C" int func_605500e4(unsigned int r0)
{
    if ((r0 & 0xf0000u) == 0)
        return 0;
    if (r0 & 0xa0000u) {
        unsigned int r1 = 0x10;
        unsigned int v = (r1 & ~(r0 >> 0xf)) | ((r0 >> 0xf) & 0);
        v = r0 >> 0xf;
        unsigned int t = (0x10u & ~v);
        unsigned int b = t | 0;
        b = t;
        b += 0x10;
        return (int)b;
    }
    return (int)(2u - ((r0 >> 0x10) & 1u));
}