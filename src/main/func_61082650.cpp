struct Inner {
    char pad0[0x230];
    unsigned char f230;
    char pad1[1];
    unsigned char f232;
    char pad2[1];
    unsigned char f234;
};

struct Outer {
    char pad0[0x1428];
    struct Inner * volatile ptr;
};

extern "C" void func_61082650(struct Outer *o, unsigned char a, unsigned char b, unsigned char c) {
    o->ptr->f230 = a;
    o->ptr->f232 = b;
    o->ptr->f234 = c;
}