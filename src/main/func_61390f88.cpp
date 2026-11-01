struct S {
    unsigned char pad_000[0xC0];
    unsigned char flag;
    unsigned char pad_0C1[0x1B];
    int arr[2];
};

extern "C" void func_61390f88(S* s, int value) {
    s->arr[s->flag == 0] = value;
}