struct Sub {
    unsigned char pad[0x4c];
    unsigned char value;
};

struct Obj {
    unsigned char pad[0x14];
    Sub *sub;
};

extern "C" void func_60160630(Obj *obj, unsigned char value) {
    Sub *sub = obj->sub;
    if (sub != 0) {
        sub->value = value;
    }
}