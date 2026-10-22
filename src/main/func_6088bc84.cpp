struct Inner {
    unsigned char pad[0xA2];
    unsigned short field;
    unsigned char pad2[0x1C];
};

struct Outer {
    unsigned char pad[0x30];
    Inner *ptr;
};

extern "C" void func_6088bc84(Outer *o, int index, unsigned short value) {
    o->ptr[index].field = value;
}