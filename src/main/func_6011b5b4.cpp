struct Arg1;

typedef void (*Fn)(Arg1*, void*);

struct Inner {
    char pad0[0xc];
    Fn fn;
};

struct Arg1 {
    Inner* inner;
};

struct Arg0 {
    char pad0[4];
    void* value;
};

extern "C" void func_6011b5b4(Arg0* a, Arg1* b) {
    Fn fn = b->inner->fn;
    void* value = a->value;
    fn(b, value);
}