struct S {
    char pad[0x504];
    unsigned char field;
};

extern "C" int func_6026fddc(S* s) {
    return (s->field >> 3) & 1;
}