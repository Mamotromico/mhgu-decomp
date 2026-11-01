struct Inner {
    unsigned char pad0[0x15ea];
    unsigned char value;
};

struct Outer {
    unsigned char pad0[0x32c8];
    Inner* inner;
};

extern "C" unsigned char func_60301294(Outer* self) {
    Inner* inner = self->inner;
    if (inner == 0) {
        return 0;
    }
    return inner->value;
}