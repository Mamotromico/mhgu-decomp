struct Inner_613206d4 {
    char pad[0x10];
    unsigned char field;
};

struct Outer_613206d4 {
    int pad;
    Inner_613206d4 *inner;
};

extern "C" int func_613206d4(Outer_613206d4 *outer) {
    Inner_613206d4 *inner = outer->inner;
    if (!inner) {
        return 0;
    }
    return inner->field != 0;
}