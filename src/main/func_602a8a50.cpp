struct Target;

struct VTable {
    unsigned char pad_0x00[0x44];
    void* (*method)(Target*, void*);
};

struct Target {
    VTable* vtable;
};

struct Host {
    unsigned char pad_0x0000[0x3190];
    Target* target;
};

extern "C" void* func_602a8a50(Host* host, void* context) {
    Target* target = host->target;
    if (target == 0) {
        return 0;
    }
    return target->vtable->method(target, context);
}