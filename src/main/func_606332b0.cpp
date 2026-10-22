struct Inner;

struct Outer {
    unsigned char pad[0x84];
    Inner *inner;
};

struct Inner {
    void (**vtable)(Inner *);
};

extern "C" void func_606332b0(Outer *outer)
{
    Inner *p = outer->inner;
    if (p != 0) {
        p->vtable[6](p);
    }
}