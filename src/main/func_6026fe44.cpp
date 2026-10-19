struct S6026fe44 {
    char pad[0x300];
    unsigned int field;
};

extern "C" int func_6026fe44(S6026fe44 *s, unsigned int mask) {
    return (s->field & mask) != 0;
}