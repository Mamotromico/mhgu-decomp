struct func_605d18cc_inner {
    unsigned char pad[0x5d];
    unsigned char value;
};

struct func_605d18cc_outer {
    unsigned char pad[0x4c];
    struct func_605d18cc_inner *ptr;
};

extern "C" void func_605d18cc(struct func_605d18cc_outer *o, unsigned char v) {
    o->ptr->value = v;
}