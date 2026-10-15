struct S {
    char pad[0x1c];
    int arr[];
};

extern "C" int func_60274ce4(struct S *s, int i) {
    return s->arr[i];
}