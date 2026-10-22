struct Outer {
    char pad[0x1428];
    char *ptr;
};

extern "C" char *func_600c2648(Outer *o) {
    char one = 1;
    char *p = o->ptr;
    p[0x5cde] = one;
    return p;
}