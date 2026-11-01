struct Inner;

struct VTable {
    char pad[0x40];
    int (*call)(Inner*);
};

struct Inner {
    VTable* vtable;
};

struct Outer {
    char pad[0x8];
    Inner* inner;
};

extern "C" int func_61390eb4(Outer* outer) {
    Inner* inner = outer->inner;
    if (inner == 0)
        return 1;
    return inner->vtable->call(inner);
}