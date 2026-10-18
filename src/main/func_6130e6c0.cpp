struct func_6130e6c0_s {
    unsigned char pad[0x5da];
    unsigned char field;
};

extern "C" int func_6130e6c0(const struct func_6130e6c0_s *s) {
    return (s->field >> 4) & 1;
}