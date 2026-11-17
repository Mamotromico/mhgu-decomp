extern "C" int func_60438e44(unsigned char *p) {
    unsigned v = *(unsigned *)(p + 4);
    unsigned hi = v & 0xff00;
    unsigned lo = v & 0xff;
    int r1 = hi > 0x200 ? 1 : 0;
    int r2 = (lo != 0x1) ? 1 : 0;
    return r2 | r1;
}