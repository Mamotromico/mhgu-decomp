struct Inner {
    char pad0[0x5df4];
    unsigned int field;
};

struct Outer {
    char pad0[0x1428];
    Inner* ptr;
};

extern "C" void func_600c0354(Outer* o, unsigned int value) {
    o->ptr->field = value;
}