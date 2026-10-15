struct S {
    char pad[0x4c0];
    int arr[];
};

extern "C" int func_600e1a84(S *s, int i) {
    return s->arr[i];
}