extern "C" unsigned char func_604d7524(unsigned char **p) {
    unsigned char *q = *p;
    unsigned char c = *q++;
    *p = q;
    return c;
}