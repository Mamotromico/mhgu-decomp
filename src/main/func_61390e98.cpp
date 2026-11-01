struct Inner;

struct VTable {
    unsigned char pad[0x44];
    int (*call)(Inner*);
};

struct Inner {
    VTable* vtable;
};

struct Outer {
    unsigned char pad[0x8];
    Inner* inner;
};

extern "C" int func_61390e98(Outer* self) {
    Inner* inner = self->inner;
    if (inner == 0) {
        return 0;
    }
    return inner->vtable->call(inner);
}