struct Target;

struct VTable {
    void* slot_0;
    void (*slot_1)(Target*);
};

struct Target {
    VTable* vtable;
};

struct Wrapper {
    unsigned char pad[0xc];
    Target* target;
};

extern "C" void func_612c77e4(Wrapper* wrapper) {
    Target* target = wrapper->target;
    if (target)
        target->vtable->slot_1(target);
}