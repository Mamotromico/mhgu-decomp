struct InnerObj {
    unsigned char pad_0x00[0x10];
    void *value_0x10;
};

struct OuterObj {
    unsigned char pad_0x00[0x6c];
    InnerObj *inner_0x6c;
};

extern "C" void *func_60cec78c(OuterObj *obj) {
    InnerObj *inner = obj->inner_0x6c;
    return inner ? inner->value_0x10 : 0;
}