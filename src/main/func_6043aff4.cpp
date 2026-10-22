struct S {
    char pad[4];
    unsigned char field; // offset 0x4
};

extern "C" int func_6043aff4(S* p) {
    return p->field == 1 ? 0 : 1;
}