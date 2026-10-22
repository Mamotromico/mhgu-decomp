struct Target;
typedef void (*TargetFn)(Target *);

struct VTable {
    char pad[0x40];
    TargetFn fn;
};

struct Target {
    VTable *vtable;
};

struct Wrapper {
    char pad[0x178];
    Target *target;
};

extern "C" void func_6055ecc8(Wrapper *self) {
    Target *target = self->target;
    if (target) {
        target->vtable->fn(target);
    }
}