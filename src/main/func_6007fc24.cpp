extern "C" void func_6007fc24(char *base, unsigned int mask) {
    unsigned short *p = *(unsigned short **)(base + 0x1428);
    p = (unsigned short *)((char *)p + 0x362);
    *p = (unsigned short)(*p & ~mask);
}