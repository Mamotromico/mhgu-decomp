struct Inner {
    char pad0[0x30];
    int field30;
};

struct Outer {
    char pad0[0xa4];
    Inner *fieldA4;
};

extern "C" int func_612b9598(Outer *o) {
    Inner *p = o->fieldA4;
    if (p == 0)
        return 0;
    return p->field30 != 5 ? 1 : 0;
}