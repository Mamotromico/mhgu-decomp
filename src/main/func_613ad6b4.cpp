struct Level3;

struct VTable {
    char pad0[0x2c];
    void (*fn)(Level3*, void*);
};

struct Level3 {
    VTable* vtable;
};

struct Level2 {
    char pad0[0x40];
    Level3* p;
};

struct Level1 {
    char pad0[0xc];
    Level2* p;
};

extern "C" void func_613ad6b4(Level1* o, void* x) {
    Level3* q = o->p->p;
    q->vtable->fn(q, x);
}