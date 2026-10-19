struct func_605bc490_inner {
    unsigned char pad0[0x4c];
    unsigned int field;
};

struct func_605bc490_outer {
    unsigned char pad0[0x9c];
    func_605bc490_inner *inner;
};

extern "C" func_605bc490_inner *func_605bc490(func_605bc490_outer *arg) {
    func_605bc490_inner *p = arg->inner;
    p->field = 0;
    return p;
}