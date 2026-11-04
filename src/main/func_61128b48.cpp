extern "C" int func_61128b48(void *p, unsigned char v) {
    unsigned char *base = *(unsigned char **)((char *)p + 0x13c4);
    unsigned char b0 = base[0x248];
    if (b0 == v) return 0;
    unsigned char b1 = base[0x249];
    if (b1 == v) return 1;
    unsigned char b2 = base[0x24a];
    if (b2 == v) return 2;
    unsigned char b3 = base[0x24b];
    if (b3 == v) return 3;
    unsigned char b4 = base[0x24c];
    if (b4 == v) return 4;
    unsigned char b5 = base[0x24d];
    if (b5 == v) return 5;
    unsigned char b6 = base[0x24e];
    if (b6 == v) return 6;
    unsigned char b7 = base[0x24f];
    if (b7 == v) return 7;
    return -1;
}