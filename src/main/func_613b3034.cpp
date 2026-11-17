extern "C" unsigned func_613b3034(char *p) {
    unsigned short v = *(unsigned short *)(p + 4);
    unsigned r2 = v + 1;
    if ((r2 & 0xffff) == 0)
        r2 = v + 2;
    *(unsigned short *)(p + 4) = (unsigned short)r2;
    return (unsigned short)r2;
}