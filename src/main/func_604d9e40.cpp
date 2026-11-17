extern "C" unsigned char *func_604d9e40(unsigned char *p, unsigned char *q, unsigned i)
{
    unsigned k = 0;
    if (q != 0) {
        unsigned short h = *(unsigned short *)(q + 4);
        if (h != 0 && h > i) {
            unsigned off = *(unsigned *)(q + 0x14 + (i << 3));
            return q + off;
        }
    }
    return (unsigned char *)k;
}