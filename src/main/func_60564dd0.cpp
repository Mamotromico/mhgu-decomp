struct S {
    char pad0[0x4c];
    unsigned int flags;
    char pad1[0x20];
    unsigned char arr[6];
};

extern "C" void func_60564dd0(S* s, unsigned int idx, unsigned char val) {
    if (idx > 5) return;
    s->flags |= 4;
    s->arr[idx] = val;
}