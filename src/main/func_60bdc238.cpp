struct Inner {
    unsigned int value;
    unsigned int pad;
};

struct Outer {
    unsigned char pad[0x24];
    Inner *arr;
};

extern "C" unsigned int func_60bdc238(Outer *o, unsigned int idx) {
    Inner *arr = o->arr;
    unsigned int v = arr[idx].value;
    return idx | (v << 12);
}