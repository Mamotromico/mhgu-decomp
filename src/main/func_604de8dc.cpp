struct Outer;

struct Vtable {
    char pad0[0x18];
    void (*fn)(Outer*);
};

struct Outer {
    Vtable * volatile vtable;
    char pad1[0x1a95 - 4];
    volatile unsigned char flag;
};

extern "C" void func_604de8dc(Outer *p) {
    p->flag = 0;
    p->vtable->fn(p);
}