struct Outer;

struct Inner {
    char pad[0x214];
    void (*fn)(Outer*, void*);
};

struct Outer {
    Inner* inner;
};

extern "C" void func_60081ff8(Outer* o, void* ctx)
{
    o->inner->fn(o, ctx);
}