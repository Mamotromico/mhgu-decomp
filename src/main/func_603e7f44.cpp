struct S {
    unsigned char pad[0x27];
    unsigned char field;
};

extern "C" void func_603e7f44(void *, struct S *p, unsigned char v) {
    p->field = v;
}