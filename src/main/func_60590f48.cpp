extern "C" {
struct S_60590f48 {
    unsigned char pad0[0x50];
    unsigned int flags;
    unsigned char pad1[0x5a - 0x54];
    unsigned char data[4];
};

void func_60590f48(S_60590f48 *s, unsigned int idx, unsigned char val) {
    if (idx > 3)
        return;
    s->data[idx] = val;
    s->flags |= 4;
}
}