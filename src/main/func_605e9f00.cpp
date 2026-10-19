extern "C" {

struct Inner {
    char pad0[0x7c];
    unsigned int value;
};

struct Outer {
    char pad0[0x4c];
    unsigned int value;
    Inner* inner;
};

Inner* func_605e9f00(Outer* outer, unsigned int value) {
    outer->value = value;
    Inner* inner = outer->inner;
    inner->value = value;
    return inner;
}

}