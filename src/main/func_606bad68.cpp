struct S {
    char pad0[0x4c];
    unsigned int flags;
    char pad1[0x3c];
    int arr[3];
};

extern "C" void func_606bad68(S *s, unsigned int index, int value) {
    s->flags |= 0x400u;
    if (index <= 2) {
        s->arr[index] = value;
    }
}