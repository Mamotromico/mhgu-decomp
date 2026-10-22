struct S {
    int field0;
    char pad[12];
    char field10;
};

extern "C" int func_613ed540(S* s) {
    s->field0 = 1;
    s->field10 = 0;
    return 1;
}