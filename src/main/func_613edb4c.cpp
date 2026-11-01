extern "C" void *func_613edb4c(char *r0, unsigned r1)
{
    unsigned r2 = *(unsigned *)(r0 + 0x5d0);
    unsigned r3 = r2 + r1;
    void *r1out = 0;
    if (r3 <= 0x5c0) {
        *(unsigned *)(r0 + 0x5d0) = r3;
        r1out = (void *)(r0 + r2 + 0x10);
    }
    return r1out;
}