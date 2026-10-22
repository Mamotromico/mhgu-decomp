extern "C" {
struct S {
    char pad0[0x54];
    int field_54;
    char pad1[0x5c - 0x54 - 4];
    int field_5c;
};

void func_6057e084(S *s, int value) {
    s->field_54 = value;
    s->field_5c |= 1;
}
}