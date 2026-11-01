struct inner {
    unsigned char pad0[0x348];
    unsigned char field0;
};

struct outer {
    unsigned char pad0[0x3ac4];
    inner *field0;
};

extern "C" int func_61128684(outer *arg0) {
    return arg0->field0->field0 == 4;
}