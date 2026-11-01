struct Dispatch {
    unsigned char pad[0x6cc];
    void (*fn)(void*, unsigned short, unsigned short);
};

struct Object {
    Dispatch* dispatch;
    unsigned char pad0[0x2502];
    unsigned short a;
    unsigned short pad1;
    unsigned short b;
};

extern "C" void func_602aa814(Object* self) {
    self->dispatch->fn(self, self->a, self->b);
}