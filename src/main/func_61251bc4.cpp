struct S {
    char pad0[0x40];
    unsigned short field;   // offset 0x40
};

extern "C" void func_61251bc4(S* s, unsigned short v) {
    s->field = v;
}