struct S {
    char pad[0x2a74];
    unsigned char field;
};

extern "C" void func_6005bb04(struct S *p, unsigned char v) {
    p->field = v;
}