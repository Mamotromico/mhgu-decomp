struct Inner {
    char pad[0x362];
    unsigned short field;
};

struct Outer {
    char pad[0x1428];
    Inner *inner;
};

extern "C" void func_6007fc40(Outer *o, unsigned int val) {
    o->inner->field |= val;
}