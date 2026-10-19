struct Inner60612718 {
    unsigned char pad[0x7c];
    unsigned int field_7c;
};

struct Outer60612718 {
    unsigned char pad[0x4c];
    Inner60612718 *field_4c;
};

extern "C" Inner60612718 *func_60612718(Outer60612718 *outer, unsigned int value) {
    Inner60612718 *inner = outer->field_4c;
    if (inner != 0) {
        inner->field_7c = value;
    }
    return inner;
}