struct S {
    unsigned char pad[0x16b5];
    unsigned char value;
};

extern "C" void func_603aeff8(S* s) {
    s->value = 1;
}