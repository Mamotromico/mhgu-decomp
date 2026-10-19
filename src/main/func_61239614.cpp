struct S {
    char pad[0x10];
    unsigned int field;
};

extern "C" void func_61239614(S *p) {
    p->field -= 1;
}