struct S {
    char pad[0x30];
    unsigned int field;
};

extern "C" void func_60921fcc(S* p) {
    p->field ^= 0x8000;
}