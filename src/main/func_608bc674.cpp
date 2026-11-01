struct S_608bc674 {
    char pad_0[0x98];
    int field_98;
    char pad_9c[0xc];
    int field_a8;
};

extern "C" int func_608bc674(S_608bc674 *s) {
    if (s->field_98 == 0)
        return 0;
    return s->field_a8 != 0;
}