struct S_6003b714 {
    unsigned char pad0[0xe5c];
    unsigned int field_0xe5c;
    unsigned char pad1[0x13c];
    unsigned int field_0xf9c;
};

extern "C" int func_6003b714(S_6003b714 *s) {
    unsigned int a = s->field_0xe5c;
    unsigned int b = s->field_0xf9c;
    int result = 0;
    if (b != a) {
        result = 1;
    }
    return result;
}