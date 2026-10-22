struct target;

struct vtable {
    char pad[0x34];
    void (*method)(target*, int, int, int);
};

struct target {
    vtable* vtbl;
};

struct holder {
    char pad[0xc];
    target* value;
};

extern "C" void func_60b22eb8(holder* h, int a, int b, int c) {
    target* t = h->value;
    t->vtbl->method(t, a, b, c);
}