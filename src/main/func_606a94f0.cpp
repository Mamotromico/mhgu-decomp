extern "C" void func_606a94f0(char *p) {
    *(unsigned *)(p + 0x34) = 0;
    *(unsigned *)(p + 0x30) = 0;
    *(unsigned *)(p + 0x2c) = 0;
    p[0x46] = 0;
    p[0x47] = 0;
    p[0x48] = 0;
    p[0x44] = 1;
    unsigned r2 = 5;
    if (*(unsigned char *)(p + 0x45) != 0) {
        r2 = 0xb;
    }
    unsigned r1 = *(unsigned char *)(p + 0x45) != 0 ? 0x42 : 0x19;
    *(unsigned *)(p + 0x38) = r2;
    *(unsigned *)(p + 0x3c) = r1;
}