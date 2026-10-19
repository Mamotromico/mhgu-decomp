struct S_60c65e38 {
    unsigned char pad[0x454];
    unsigned int field;
};

extern "C" void func_60c65e38(S_60c65e38* s, unsigned int a, unsigned int b) {
    s->field = (a & 0xFFFFu) | (b << 16);
}