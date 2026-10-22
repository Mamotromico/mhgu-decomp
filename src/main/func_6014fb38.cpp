struct S {
    unsigned char padding[0x38];
    unsigned int value;
};

extern "C" int func_6014fb38(S* s) {
    return (s->value - 0x70u) < 3u;
}