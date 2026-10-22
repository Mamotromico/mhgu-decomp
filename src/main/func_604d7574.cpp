extern "C" int func_604d7574(short **p) {
    short *q = *p;
    short v = *q++;
    *p = q;
    return v;
}