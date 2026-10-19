struct S6055efe8 {
    char pad[0x188];
    unsigned int field;
};

extern "C" int func_6055efe8(S6055efe8 *p) {
    return p->field != 0;
}