struct S6006bbe8 {
    char pad[0x1053];
    unsigned char value;
};

extern "C" void func_6006bbe8(S6006bbe8 *s, unsigned char v) {
    s->value = v;
}