struct S {
    char pad[0x18];
    float f;
};

extern "C" void func_6124b428(S* s, float v) {
    s->f = v;
}