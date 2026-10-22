struct S605584e0 {
    char pad0[0x19];
    unsigned char field19;
    char pad1[0x1];
    unsigned char field1b;
};

extern "C" void func_605584e0(S605584e0* s) {
    s->field19 = 0;
    s->field1b = 1;
}