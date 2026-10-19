struct S_600b1534 {
    unsigned char pad0[0x13a4];
    float value;
};

extern "C" void func_600b1534(S_600b1534 *s) {
    s->value = 1.0f;
}