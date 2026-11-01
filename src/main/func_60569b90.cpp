struct func_60569b90_s {
    unsigned char pad_0[0xb8];
    unsigned int flags;
    unsigned char pad_1[0xe4 - 0xbc];
    unsigned int arr[4];
    unsigned int pad_2;
    unsigned int value;
};

extern "C" void func_60569b90(func_60569b90_s *s, unsigned int a, unsigned int b, unsigned int idx)
{
    if (idx <= 3u)
        s->arr[idx] = a;
    s->value = b;
    s->flags |= 0x30u;
}