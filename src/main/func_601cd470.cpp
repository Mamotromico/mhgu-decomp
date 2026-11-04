extern "C" void func_601cd470(char *p) {
    unsigned short v = 0xff7f;
    unsigned int i;
    for (i = 4; i <= 0x18; i += 4) {
        char *q = *(char **)(p + i);
        if (q && *(unsigned int *)(q + 0x10) == 1) {
            *(unsigned short *)(q + 0x8) = v;
            *(unsigned short *)(q + 0xa) = v;
            *(unsigned short *)(q + 0xc) = v;
            *(unsigned short *)(q + 0xe) = v;
        }
    }
}