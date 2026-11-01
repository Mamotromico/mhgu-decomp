struct Func600e8858Arg {
    unsigned char pad[0x241];
    unsigned char field;
};

extern "C" int func_600e8858(const Func600e8858Arg *arg, unsigned int value) {
    unsigned int limit = (arg->field == 0) ? 1 : 2;
    return limit > value;
}