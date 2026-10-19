struct S {
    unsigned char pad[0x68];
    unsigned int field_0x68;
};

extern "C" void func_605f7970(S* s) {
    s->field_0x68 |= 4u;
}