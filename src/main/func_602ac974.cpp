struct Vtable {
    char pad[0x394];
    void (*fn)(void*, int, void*, int);
};

struct Object {
    Vtable* vtable;
};

extern "C" void func_602ac974(Object* self) {
    self->vtable->fn(self, 0x89, (char*)self + 0x2550, 1);
}