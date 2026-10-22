struct S {
    char pad[0x1a2];
    unsigned short field;
};

extern "C" void func_605045b0(struct S *s) {
    s->field |= 0x100;
}