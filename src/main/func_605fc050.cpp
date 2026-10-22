struct S {
    unsigned char pad0[0x58];
    unsigned char flags;
    unsigned char pad1[0x5];
    unsigned char byte5e;
};

extern "C" void func_605fc050(S* s, unsigned char value) {
    s->flags |= 0x20u;
    s->byte5e = value;
}