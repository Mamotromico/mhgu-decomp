struct Inner_60071244 {
    unsigned char pad[0x64];
    float value;
};

struct Outer_60071244 {
    unsigned char pad[0x75e8];
    Inner_60071244 *inner;
};

extern "C" float func_60071244(Outer_60071244 *obj) {
    return obj->inner->value;
}