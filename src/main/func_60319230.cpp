struct func_60319230_s {
    char pad[0x5c];
    unsigned int field;
};

extern "C" int func_60319230(func_60319230_s *s) {
    return s->field == 2 ? 1 : 0;
}