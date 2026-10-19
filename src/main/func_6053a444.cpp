struct S6053a444 {
    char pad[0x638];
    float value;
};

extern "C" float func_6053a444(S6053a444* p) {
    return p->value;
}