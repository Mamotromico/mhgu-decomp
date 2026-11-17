extern "C" void func_603a4530(unsigned char *base, unsigned bit, unsigned index, unsigned off) {
    unsigned char *p = base + index * 5 + off;
    p = (unsigned char *)((char *)p + 0x1554);
    *p = (unsigned char)((*p) | (1u << bit));
}