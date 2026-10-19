extern "C" {
struct S {
    unsigned char pad[0x178];
    int field;
};

int func_6055ecb8(S* s) {
    return s->field != 0;
}
}