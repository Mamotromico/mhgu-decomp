struct S_60282420 {
    unsigned char pad[0x14b8];
    unsigned int field_14b8;
    unsigned int field_14bc;
};

extern "C" void func_60282420(S_60282420 *s) {
    s->field_14bc = s->field_14b8;
}