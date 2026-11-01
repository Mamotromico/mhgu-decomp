extern "C" unsigned int func_603a8b54(const unsigned char *p) {
    unsigned int r0 = 1;
    if (p[0xee] & 8)
        return r0;
    if (!(p[0xfa] & 8)) {
        r0 = p[0x106];
        r0 = (r0 >> 3) & 1;
    }
    return r0;
}