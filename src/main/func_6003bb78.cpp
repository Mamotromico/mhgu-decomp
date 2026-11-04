extern "C" {

struct Inner {
    unsigned int count;
    unsigned int *ids;
    char pad_0x8[0xc - 0x8];
    unsigned int base;
};

struct Outer {
    char pad_0x0[0xecc];
    Inner *inner;
};

unsigned int func_6003bb78(Outer *o, unsigned int id) {
    Inner *in = o->inner;
    unsigned int result = 0;
    if (in != 0 && in->count != 0) {
        unsigned int *arr = in->ids;
        unsigned int i = 0;
        unsigned int off = 0;
        unsigned int n = in->count;
        do {
            unsigned int v = arr[i];
            if (v == id) {
                return in->base + off;
            }
            i++;
            off += 0x110;
        } while (i < n);
    }
    return result;
}

}