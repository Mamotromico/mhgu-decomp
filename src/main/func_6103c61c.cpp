struct Inner {
    unsigned char pad[0x1bb];
    unsigned char flags;
};

struct Outer {
    unsigned char pad[0x1428];
    Inner* ptr;
};

extern "C" int func_6103c61c(Outer* outer) {
    return outer->ptr->flags & 1;
}