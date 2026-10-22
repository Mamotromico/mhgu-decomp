struct S_6057e098 {
    unsigned char pad[0x58];
    int field_58;
    int field_5c;
};

extern "C" void func_6057e098(S_6057e098* s, int value) {
    s->field_58 = value;
    s->field_5c |= 2;
}