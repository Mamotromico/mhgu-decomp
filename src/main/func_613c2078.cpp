extern "C" int func_613c2078(char *a, unsigned *out1, unsigned long long *out2) {
    int result = -1;
    if (*(unsigned char *)(a + 0x11e))
        return result;
    unsigned head = *(unsigned *)(a + 0x438);
    unsigned tail = *(unsigned *)(a + 0x43c);
    result = 0;
    if (head == tail)
        return result;
    unsigned idx = (head + 1) & 0xf;
    char *e = a + (unsigned)(idx + idx * 2) * 8;
    unsigned tag = *(unsigned *)(e + 0x2cc);
    if (tag == 4) {
        *(unsigned char *)(a + 0x11e) = 1;
        return -1;
    }
    *out1 = *(unsigned *)(e + 0x2b8);
    unsigned lo = *(unsigned *)(e + 0x2c0);
    unsigned hi = *(unsigned *)(e + 0x2c4);
    *out2 = ((unsigned long long)hi << 32) | lo;
    return *(int *)(e + 0x2c8);
}