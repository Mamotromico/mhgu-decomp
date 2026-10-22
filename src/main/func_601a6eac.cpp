struct S_601a6eac {
    unsigned char pad[0x1e];
    unsigned char field;
};

extern "C" int func_601a6eac(const S_601a6eac *s) {
    return s->field == 2;
}