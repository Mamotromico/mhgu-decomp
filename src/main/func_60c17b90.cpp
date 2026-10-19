struct func_60c17b90_s {
    unsigned char pad[0x7c];
    unsigned int field;
};

extern "C" int func_60c17b90(const func_60c17b90_s *p) {
    return p->field == 1;
}