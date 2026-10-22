struct Inner_60081fb0 {
    unsigned char pad0[0x523];
    unsigned char value;
};

struct Outer_60081fb0 {
    unsigned char pad0[0x1428];
    Inner_60081fb0 *ptr;
};

extern "C" int func_60081fb0(Outer_60081fb0 *obj) {
    return obj->ptr->value != 0;
}