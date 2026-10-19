struct S {
    unsigned char pad0[0xc0];
    unsigned char index;
    unsigned char pad1[0x1b];
    unsigned int values[1];
};

extern "C" void func_61390f78(S* s, unsigned int value) {
    s->values[s->index] = value;
}