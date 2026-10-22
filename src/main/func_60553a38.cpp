struct S {
    unsigned char pad[0x10];
    unsigned int bits;
};

extern "C" void func_60553a38(S* s, unsigned int bit) {
    s->bits &= ~(1u << bit);
}