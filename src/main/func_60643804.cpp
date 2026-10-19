struct S {
    unsigned char pad[0x298];
    unsigned int value;
};

extern "C" void func_60643804(S *s, unsigned int v) {
    if (s->value != v)
        s->value = v;
}