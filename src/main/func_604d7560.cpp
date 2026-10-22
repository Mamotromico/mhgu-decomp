extern "C" int func_604d7560(signed char **p) {
    signed char *q = *p;
    int c = *q++;
    *p = q;
    return c;
}