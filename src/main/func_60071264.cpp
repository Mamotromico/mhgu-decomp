struct inner_60071264 {
    char pad0[0x69];
    unsigned char field;
};

struct outer_60071264 {
    char pad0[0x75e8];
    struct inner_60071264 *ptr;
};

extern "C" unsigned char func_60071264(struct outer_60071264 *arg) {
    return arg->ptr->field;
}