struct S {
    unsigned char pad[0x2518];
    float values[1];
};

extern "C" void func_6005d760(S *s, int index, float value) {
    float *p = s->values + index;
    if (*p < value) {
        *p = value;
    }
}