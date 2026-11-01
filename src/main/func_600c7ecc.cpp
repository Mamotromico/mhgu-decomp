extern "C" unsigned char func_600c7ecc(unsigned char *base, unsigned int index) {
    unsigned int *slot = (unsigned int *)(base + 0x1428);
    unsigned char *p = (unsigned char *)(*slot + index);
    unsigned char v = p[0x234];
    if (v != 0xff) {
        if (p[0x230] != 0x1)
            v = 0xff;
    }
    return v;
}