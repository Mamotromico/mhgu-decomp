struct S_603a24a0 {
    unsigned char pad[0x50];
    unsigned char value;
};

extern "C" void func_603a24a0(S_603a24a0* s, unsigned int x) {
    if (x <= 9u) {
        s->value = x;
    }
}