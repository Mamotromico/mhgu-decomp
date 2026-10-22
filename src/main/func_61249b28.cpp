struct Inner {
    char pad[0x40];
    void (*method)(void*, void*);
};

struct Middle {
    Inner* inner;
};

struct Outer {
    char pad[4];
    Middle* middle;
};

extern "C" void func_61249b28(Outer* self)
{
    Middle* m = self->middle;
    m->inner->method(m, self);
}