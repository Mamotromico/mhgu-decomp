struct S_605f12a4 {
    unsigned char pad[0x50];
    unsigned int value;
    unsigned int flags;
};

extern "C" void func_605f12a4(S_605f12a4 *s, unsigned int value) {
    unsigned int flags = s->flags;
    s->value = value;
    flags |= 2u;
    s->flags = flags;
}