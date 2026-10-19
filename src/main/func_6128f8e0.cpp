struct S {
    int pad0;
    void *field4;
};

extern "C" void *func_6128f8e0(S *s, int index) {
    return (char *)s->field4 + index * 0x2c;
}