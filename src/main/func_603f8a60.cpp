struct S {
    unsigned char pad[0x7b];
    unsigned char field;
};

extern "C" unsigned int func_603f8a60(const S* s, unsigned int mask) {
    return (s->field & mask) ? 1u : 0u;
}