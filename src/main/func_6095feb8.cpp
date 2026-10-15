struct S {
    unsigned char _pad0[0x60];
    float value;
};

extern "C" void func_6095feb8(S *s, float v) {
    s->value = v;
}