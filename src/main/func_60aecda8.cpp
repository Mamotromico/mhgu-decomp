struct Inner {
    char pad0[0x30];
    void *field30;
};

struct Outer {
    char pad0[0x28];
    Inner *inner28;
};

extern "C" void *func_60aecda8(Outer *p) {
    if (p->inner28)
        return p->inner28->field30;
    return 0;
}