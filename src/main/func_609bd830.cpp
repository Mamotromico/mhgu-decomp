struct S_609bd830 {
    unsigned char pad[0x1bb];
    unsigned char field;
};

extern "C" void func_609bd830(S_609bd830* dst, const S_609bd830* src) {
    dst->field = (unsigned char)(src->field + 1);
}