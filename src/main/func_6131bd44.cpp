struct S {
    char pad[0x2c];
    unsigned char arr[1];
};

extern "C" unsigned char func_6131bd44(S *s, int i) {
    return s->arr[i];
}