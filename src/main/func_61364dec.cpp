struct Inner {
    unsigned char pad0;
    unsigned char field1;
    unsigned short field2;
};

struct Outer {
    unsigned char pad0[4];
    Inner *field4;
    unsigned char pad8[2];
    unsigned char fieldA;
    unsigned char padB[3];
    unsigned short fieldE;
};

extern "C" int func_61364dec(Outer *outer) {
    Inner *inner = outer->field4;
    outer->fieldA = inner->field1;
    outer->fieldE = inner->field2;
    return 1;
}