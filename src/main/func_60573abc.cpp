extern "C" {

struct S {
    char pad0[0x74];
    int flags;
    int arr[5];
    int field8c;
};

void func_60573abc(S* s, int a, int b, int idx) {
    s->arr[idx] = a;
    s->field8c = b;
    s->flags |= 0x30;
}

}