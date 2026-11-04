extern "C" int func_612a9f80(unsigned char *p)
{
    unsigned int *q = *(unsigned int **)(p + 0x8);
    unsigned int off = *(unsigned int *)(p + 0xc);
    unsigned int other = *(unsigned int *)(q + 0x4);
    if (other - off <= 3) {
        p[4] = 1;
        return 0;
    }
    unsigned char *base = (unsigned char *)*(unsigned int *)(q + 0x3) +
                          *(unsigned int *)(q + 0x6);
    unsigned int b0 = base[off];
    unsigned int b1 = base[off + 1];
    unsigned int b2 = base[off + 2];
    unsigned int b3 = base[off + 3];
    *(unsigned int *)(p + 0xc) = off + 4;
    return (int)(b0 | (b1 << 8) | (b2 << 16) | (b3 << 24));
}