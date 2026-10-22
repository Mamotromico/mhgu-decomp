struct Inner60194c80 {
    char pad0[0x64];
    int value;
};

struct Outer60194c80 {
    char pad0[0x20];
    Inner60194c80 *inner;
};

extern "C" int func_60194c80(Outer60194c80 *o) {
    Inner60194c80 *p = o->inner;
    if (p == 0) {
        return 0;
    }
    return p->value;
}