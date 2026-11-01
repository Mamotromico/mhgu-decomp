struct Inner {
    char pad[0x10];
    unsigned char field;
};

struct Outer {
    char pad[0x40];
    Inner *ptr;
};

extern "C" int func_613720ec(Outer *o) {
    Inner *p = o->ptr;
    if (p != 0 && p->field != 0) {
        return 1;
    }
    return 0;
}