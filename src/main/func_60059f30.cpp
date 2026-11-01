struct Inner8 {
    unsigned char pad0[8];
    unsigned char field_8;
};

struct Outer14 {
    unsigned char pad0[0x14];
    Inner8 **array;
};

extern "C" int func_60059f30(Outer14 *outer, unsigned int index) {
    Inner8 *item = outer->array[index];
    return item && item->field_8;
}