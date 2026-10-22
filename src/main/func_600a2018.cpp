struct Inner_600a2018 {
    unsigned char pad0[0x5e09];
    unsigned char field;
};

struct Outer_600a2018 {
    unsigned char pad0[0x1428];
    Inner_600a2018 *inner;
};

extern "C" int func_600a2018(Outer_600a2018 *arg0, unsigned int arg1) {
    return (arg0->inner->field & arg1) != 0;
}