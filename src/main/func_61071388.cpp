struct Inner {
    unsigned char pad[0x1bb];
    unsigned char field;
};

struct Outer {
    unsigned char pad[0x1428];
    Inner* ptr;
};

extern "C" unsigned int func_61071388(Outer* o) {
    return (o->ptr->field >> 2) & 1u;
}