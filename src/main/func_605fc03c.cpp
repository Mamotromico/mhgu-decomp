struct S {
    unsigned char pad[0x58];
    unsigned char f58;
    unsigned char pad2[0x5d - 0x59];
    unsigned char f5d;
};

extern "C" void func_605fc03c(S* s, unsigned char v) {
    s->f58 |= 0x18;
    s->f5d = v;
}