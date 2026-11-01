struct S {
    unsigned char pad_0[0xb8];
    unsigned int flags;
    unsigned char pad_bc[0x28];
    unsigned int arr[4];
    unsigned char pad_f4[0x04];
    unsigned int value_f8;
};

extern "C" void func_60569b70(S *s, unsigned int a, unsigned int b, unsigned int idx)
{
    if (idx <= 3u) {
        s->arr[idx] = a;
    }
    s->value_f8 = b;
    s->flags |= 0x30u;
}