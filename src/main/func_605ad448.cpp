struct S {
    unsigned char pad[0x52];
    unsigned char field;
};

extern "C" void func_605ad448(S* s) {
    if (++s->field == 3) {
        s->field = 0;
    }
}