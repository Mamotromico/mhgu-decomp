struct S {
    unsigned char pad[0x3330];
    unsigned char b;
};

extern "C" unsigned int func_611e2204(const S* s) {
    return (s->b >> 1) & 1u;
}