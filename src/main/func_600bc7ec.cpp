struct S {
    char pad[0x1428];
    int* arr;
};

extern "C" int func_600bc7ec(S* s, int idx) {
    return s->arr[idx + 0x9d];
}