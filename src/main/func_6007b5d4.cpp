struct Inner_6007b5d4 {
    char pad[0x10];
    int f10;
    int f14;
    int f18;
};

struct Outer_6007b5d4 {
    char pad[0x1428];
    Inner_6007b5d4 * volatile p;
};

extern "C" void func_6007b5d4(Outer_6007b5d4 *o) {
    o->p->f10 = 0;
    o->p->f14 = 0;
    o->p->f18 = 0;
}