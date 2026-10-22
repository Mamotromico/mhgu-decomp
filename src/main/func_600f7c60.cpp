struct B;
struct A { char pad[4]; void *value; };
struct VTable { char pad[12]; void (*fn)(B *, void *); };
struct B { VTable *vtable; };

extern "C" void func_600f7c60(A *a, B *b) {
    b->vtable->fn(b, a->value);
}