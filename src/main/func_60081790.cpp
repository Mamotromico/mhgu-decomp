struct Inner60081790 {
    unsigned char pad[0x5df3];
    unsigned char value;
};

struct Outer60081790 {
    unsigned char pad[0x1428];
    Inner60081790 *ptr;
};

extern "C" unsigned char func_60081790(Outer60081790 *obj) {
    return obj->ptr->value;
}