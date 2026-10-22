struct S_602a9abc {
    unsigned char pad[0x32a0];
    unsigned short field;
};

extern "C" int func_602a9abc(S_602a9abc *s) {
    return s->field == 2;
}