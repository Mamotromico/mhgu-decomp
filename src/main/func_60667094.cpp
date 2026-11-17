extern "C" unsigned func_60667094(unsigned a, unsigned b) {
    unsigned r;
    if (a == 3)
        r = 0xf0;
    else if (a == 2) {
        r = 0x50;
        if (b == 4)
            r = 0xf0;
    } else
        r = 0x3c0;
    return r;
}