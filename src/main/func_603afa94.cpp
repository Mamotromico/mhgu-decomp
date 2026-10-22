struct S {
    char pad[0xad];
    signed char field_ad;
    signed char field_ae;
};

extern "C" char *func_603afa94(S *s) {
    return reinterpret_cast<char *>(s) + (s->field_ae << 5) + (s->field_ad << 2) + 0xc;
}