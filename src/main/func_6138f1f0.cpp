struct Inner;

struct VTable {
    unsigned char pad[0x2c];
    int (*method)(Inner*);
};

struct Inner {
    VTable* vptr;
};

struct Outer {
    unsigned char pad[8];
    Inner* inner;
};

extern "C" int func_6138f1f0(Outer* outer) {
    Inner* inner = outer->inner;
    if (inner == 0)
        return 0;
    return inner->vptr->method(inner);
}