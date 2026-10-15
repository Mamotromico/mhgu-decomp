struct S {
    unsigned char pad[0x6c];
    float value;
};

extern "C" void func_6095fed0(struct S *p, float v) {
    p->value = v;
}