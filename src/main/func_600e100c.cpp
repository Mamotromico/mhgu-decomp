struct S {
    int pad0;
    unsigned short arr[1];
};

extern "C" unsigned short func_600e100c(struct S *s, int i) {
    return s->arr[i];
}