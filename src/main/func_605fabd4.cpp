struct S_605fabd4 {
    char pad[0x5d];
    unsigned int field;
} __attribute__((packed));

extern "C" void func_605fabd4(S_605fabd4 *s) {
    s->field = 0;
}