struct inner_61127cb4 {
    char pad[0x3c8];
    unsigned int value;
};

struct outer_61127cb4 {
    char pad[0x3328];
    inner_61127cb4 *inner;
};

extern "C" int func_61127cb4(outer_61127cb4 *o, unsigned int mask) {
    return (o->inner->value & mask) != 0;
}