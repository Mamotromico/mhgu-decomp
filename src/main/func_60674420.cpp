extern "C" void *func_6065cb3c(void *, int);

extern "C" void func_60674420(void *p, unsigned char c) {
    unsigned char *q = (unsigned char *)func_6065cb3c(p, 0xc);
    if (q)
        q[0x72] = c;
}