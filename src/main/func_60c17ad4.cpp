struct S {
    char pad[0x50];
    int field;
};

extern "C" void func_60c17ad4(S* p, unsigned int value, int mode) {
    if (mode == 1) {
        if (p->field < 0)
            value |= 0x80000000u;
    }
    p->field = value;
}