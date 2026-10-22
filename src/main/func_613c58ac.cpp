struct S {
    char pad[0x420];
    unsigned int field;
};

extern "C" int func_613c58ac(S* s) {
    return s->field != 2;
}