struct S {
    unsigned char pad[0x40];
    unsigned int value;
};

extern "C" int func_612a64a8(S *s, unsigned int mask) {
    return (s->value & mask) == mask;
}