struct Inner {
    char pad0[0x94];
    unsigned int value;
};

struct Outer {
    char pad0[0x75ec];
    Inner* inner;
};

extern "C" unsigned int func_600711e8(Outer* o) {
    return o->inner->value;
}