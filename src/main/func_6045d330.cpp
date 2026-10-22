struct S {
    unsigned char pad[4];
    unsigned char value;
};

extern "C" int func_6045d330(S* s) {
    unsigned v = s->value;
    return (v - 3) < 3;
}