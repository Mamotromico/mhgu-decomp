struct Inner {
    unsigned char pad[0x220];
    unsigned int flag;
};

struct Outer {
    Inner *inner;
};

extern "C" char *func_6139e488(Outer *outer) {
    Inner *inner = outer->inner;
    if (inner->flag != 0) {
        return reinterpret_cast<char *>(inner) + 0x21c;
    }
    return 0;
}