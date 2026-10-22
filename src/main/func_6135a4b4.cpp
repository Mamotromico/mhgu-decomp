extern "C" {
struct S_6135a4b4 {
    char pad[0x44];
    unsigned int field;
};
void func_6135a4b4(S_6135a4b4* s, unsigned int bit) {
    s->field &= ~(1u << bit);
}
}