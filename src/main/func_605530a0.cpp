struct S {
    char pad[0x10];
    unsigned int field;
};

extern "C" void func_605530a0(S* p) {
    p->field |= 3u;
}