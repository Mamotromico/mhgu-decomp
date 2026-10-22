struct Inner {
    char pad[0x2f8];
    void (*fn)(void*, int, int, int);
};

struct Outer {
    Inner* inner;
};

extern "C" void func_6028eb08(void* self) {
    Outer* o = (Outer*)self;
    o->inner->fn(self, 1, 0x412, 0x20);
}