struct S {
    char pad[8];
    unsigned short field8;
    unsigned char fieldA;
};

extern "C" void func_61374504(S* s, unsigned short value) {
    s->field8 = value;
    s->fieldA = 1;
}