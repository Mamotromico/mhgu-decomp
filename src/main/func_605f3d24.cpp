extern "C" void func_605f3d24(void *arg) {
    struct S {
        unsigned char pad[0x68];
        unsigned int field;
    };
    struct S *s = (struct S *)arg;
    s->field |= 7;
}