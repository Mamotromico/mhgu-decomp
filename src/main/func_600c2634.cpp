struct inner_600c2634 {
    unsigned char pad[0x5cb8];
    unsigned char value;
};

struct outer_600c2634 {
    unsigned char pad[0x1428];
    struct inner_600c2634 *inner;
};

extern "C" void func_600c2634(struct outer_600c2634 *outer, unsigned char value) {
    outer->inner->value = value;
}