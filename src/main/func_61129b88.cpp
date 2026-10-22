struct S {
    unsigned char pad[0x3ac4];
    unsigned char *ptr;
};

extern "C" int func_61129b88(S *s) {
    return s->ptr[0] != 0;
}