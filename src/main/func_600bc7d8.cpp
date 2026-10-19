struct Outer {
    char pad[0x1428];
    int *p;
};

extern "C" int func_600bc7d8(Outer *o, int idx) {
    return o->p[idx + 0x99];
}