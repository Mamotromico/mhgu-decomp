struct Outer;

typedef void (*Fn)(Outer *, int);

struct Inner {
    char pad[0x58];
    Fn fn;
};

struct Outer {
    Inner *p;
};

extern "C" void func_60070830(Outer *o, int x) {
    o->p->fn(o, x);
}